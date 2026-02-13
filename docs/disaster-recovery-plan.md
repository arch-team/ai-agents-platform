# 灾备演练方案

> **版本**: v1.0
> **最后更新**: 2026-02-14
> **适用范围**: AI Agents Platform (us-east-1)

---

## 1. 概述

### 1.1 恢复目标

| 指标 | 目标 | 说明 |
|------|------|------|
| **RPO** (Recovery Point Objective) | < 5 分钟 | 数据丢失容忍度 — 最多丢失最近 5 分钟数据 |
| **RTO** (Recovery Time Objective) | < 15 分钟 | 服务恢复时间 — 从故障发生到服务可用 |

### 1.2 基础设施概览

| 组件 | Dev 环境 | Prod 环境 |
|------|---------|----------|
| **Aurora MySQL** | db.t3.medium 单实例 | db.r6g.large Writer + Reader 多 AZ |
| **S3 知识库** | 已启用版本控制 + KMS 加密 | 已启用版本控制 + KMS 加密 |
| **ECS Fargate** | 256 CPU / 512 MiB / 1 任务 | 512 CPU / 1024 MiB / 2 任务 |
| **AgentCore** | AWS 托管服务 | AWS 托管服务 |
| **监控** | CloudWatch Dashboard + SNS | CloudWatch Dashboard + SNS + Performance Insights |

### 1.3 Stack 命名规范

所有 Stack 使用 `ai-agents-plat-{stack}-{env}` 命名格式:
- `ai-agents-plat-network-{dev|prod}`
- `ai-agents-plat-security-{dev|prod}`
- `ai-agents-plat-database-{dev|prod}`
- `ai-agents-plat-compute-{dev|prod}`
- `ai-agents-plat-agentcore-{dev|prod}`
- `ai-agents-plat-monitoring-{dev|prod}`

---

## 2. 数据层灾备

### 2.1 Aurora MySQL

#### 备份策略

| 备份类型 | 配置 | RPO |
|---------|------|-----|
| **连续备份 (PITR)** | Aurora 自动连续备份到 S3 | ≈ 0 (秒级精度) |
| **自动快照** | Dev 保留 7 天 / Prod 保留 30 天 | = 快照间隔 |
| **手动快照** | 按需创建，无过期 | = 创建时间点 |

**CDK 配置参考** (`infra/lib/constructs/aurora/aurora.construct.ts`):
```typescript
backup: {
  retention: isProd(envName) ? cdk.Duration.days(30) : cdk.Duration.days(7),
}
```

#### 高可用配置

- **Prod**: Writer + Reader 多 AZ，自动故障转移 (AZ 级故障 RTO < 30 秒)
- **Dev**: 单实例，无自动故障转移

#### 恢复策略

**策略 A: 时间点恢复 (PITR) — 首选**

适用场景: 数据误删、逻辑错误、需要恢复到精确时间点

RPO: ≈ 0 (可恢复到最近 5 秒内的任意时间点)

恢复步骤:

1. **确定恢复时间点**
   ```bash
   # 查看集群最早可恢复时间
   aws rds describe-db-clusters \
     --db-cluster-identifier <CLUSTER_ID> \
     --query 'DBClusters[0].{EarliestRestorableTime:EarliestRestorableTime, LatestRestorableTime:LatestRestorableTime}'
   ```

2. **执行时间点恢复**
   ```bash
   aws rds restore-db-cluster-to-point-in-time \
     --source-db-cluster-identifier <CLUSTER_ID> \
     --db-cluster-identifier <CLUSTER_ID>-pitr-restore \
     --restore-to-time "2026-02-14T10:30:00Z" \
     --vpc-security-group-ids <SECURITY_GROUP_ID> \
     --db-subnet-group-name <SUBNET_GROUP_NAME>
   ```

3. **创建实例并等待可用**
   ```bash
   aws rds create-db-instance \
     --db-instance-identifier <CLUSTER_ID>-pitr-restore-writer \
     --db-cluster-identifier <CLUSTER_ID>-pitr-restore \
     --db-instance-class db.t3.medium \
     --engine aurora-mysql

   aws rds wait db-instance-available \
     --db-instance-identifier <CLUSTER_ID>-pitr-restore-writer
   ```

4. **验证数据完整性**
   ```bash
   # 连接恢复的集群，执行数据校验
   mysql -h <RESTORED_ENDPOINT> -u admin -p \
     -e "SELECT COUNT(*) FROM agents; SELECT COUNT(*) FROM users;"
   ```

5. **切换应用连接** (如需替换原集群)
   - 更新 Secrets Manager 中的数据库连接信息
   - 或重新部署 CDK Stack 指向新集群

6. **清理旧集群** (确认恢复成功后)

**策略 B: 快照恢复**

适用场景: 集群完全损坏、需要恢复到已知良好状态

RPO: = 最近快照创建时间 (自动快照约每日一次)

恢复步骤: 参见 `scripts/dr-aurora-restore.sh` 验证脚本

**策略 C: 跨区域恢复** (当前未配置，未来增强)

适用场景: 整个 Region 不可用

前提: 需配置跨区域快照复制

### 2.2 S3 知识库文档

#### 保护策略

| 特性 | 配置 | 说明 |
|------|------|------|
| **版本控制** | 已启用 | 每次覆盖保留历史版本 |
| **KMS 加密** | CMK (Prod) / S3 Managed (Dev) | 静态数据加密 |
| **旧版本过期** | 30 天 | 自动清理 30 天前的非当前版本 |
| **公开访问** | 全部阻止 | `BlockPublicAccess.BLOCK_ALL` |

**Bucket 命名**: `ai-agents-platform-knowledge-{dev|prod}`

#### 恢复策略

**场景 1: 文件误删除**

S3 版本控制下，删除操作会创建删除标记 (Delete Marker)，原始数据仍保留。

```bash
# 查看对象的所有版本 (包括删除标记)
aws s3api list-object-versions \
  --bucket ai-agents-platform-knowledge-<ENV> \
  --prefix "path/to/deleted-file.pdf"

# 移除删除标记即可恢复
aws s3api delete-object \
  --bucket ai-agents-platform-knowledge-<ENV> \
  --key "path/to/deleted-file.pdf" \
  --version-id <DELETE_MARKER_VERSION_ID>
```

**场景 2: 文件误覆盖**

```bash
# 列出历史版本
aws s3api list-object-versions \
  --bucket ai-agents-platform-knowledge-<ENV> \
  --prefix "path/to/file.pdf"

# 将旧版本复制为当前版本
aws s3api copy-object \
  --bucket ai-agents-platform-knowledge-<ENV> \
  --copy-source "ai-agents-platform-knowledge-<ENV>/path/to/file.pdf?versionId=<OLD_VERSION_ID>" \
  --key "path/to/file.pdf"
```

**场景 3: 批量恢复**

参见 `scripts/dr-s3-rollback.sh` 验证脚本

---

## 3. 计算层灾备

### 3.1 ECS Fargate

#### 特性

- **无状态服务**: 容器不持久化数据，所有状态存储在 Aurora 和 S3
- **容器镜像**: 存储在 ECR，与 ECS 服务独立
- **自动恢复**: ECS 服务调度器自动维持期望任务数

#### 恢复策略

**场景 1: 单个任务故障**

ECS 服务自动检测并替换不健康任务，无需人工干预。

RTO: < 2 分钟 (新任务拉取镜像 + 启动)

**场景 2: 服务不可用 (需要重新部署)**

```bash
# 方案 A: 强制新部署 (滚动更新)
aws ecs update-service \
  --cluster ai-agents-plat-compute-<ENV> \
  --service <SERVICE_NAME> \
  --force-new-deployment

# 方案 B: 通过 CDK 重新部署
cd infra && pnpm cdk deploy ai-agents-plat-compute-<ENV> --context env=<ENV>
```

RTO: < 5 分钟

**场景 3: 回滚到上一版本**

```bash
# 查看部署历史
aws ecs describe-services \
  --cluster ai-agents-plat-compute-<ENV> \
  --services <SERVICE_NAME> \
  --query 'services[0].deployments'

# 更新服务使用旧的任务定义
aws ecs update-service \
  --cluster ai-agents-plat-compute-<ENV> \
  --service <SERVICE_NAME> \
  --task-definition <PREVIOUS_TASK_DEFINITION_ARN>
```

### 3.2 AgentCore Runtime

AgentCore 是 AWS 托管服务，AWS 负责其可用性和灾备。

**恢复策略**: 重新部署 CDK Stack

```bash
cd infra && pnpm cdk deploy ai-agents-plat-agentcore-<ENV> --context env=<ENV>
```

---

## 4. 演练计划

### 4.1 季度演练项目

| # | 演练项 | 频率 | 验证目标 | 预期 RTO | 验证脚本 |
|---|--------|------|---------|---------|----------|
| 1 | Aurora PITR 恢复 | 季度 | RPO < 5 分钟 | < 15 分钟 | 手动执行 |
| 2 | Aurora 快照恢复 | 季度 | RTO < 15 分钟 | < 15 分钟 | `scripts/dr-aurora-restore.sh` |
| 3 | S3 版本回滚 | 季度 | 文档可恢复 | < 2 分钟 | `scripts/dr-s3-rollback.sh` |
| 4 | ECS 服务重建 | 半年 | 计算层 RTO | < 5 分钟 | 手动执行 |

### 4.2 演练环境

- **所有演练在 Dev 环境执行**，避免影响 Prod
- 演练恢复的集群/资源使用 `-dr-test` 后缀命名
- 演练完成后必须清理所有临时资源

### 4.3 演练执行清单

#### 演练前准备

- [ ] 确认 AWS CLI 已配置正确凭证
- [ ] 确认操作者具有 RDS / S3 / ECS 所需 IAM 权限
- [ ] 确认演练时间窗口 (避开业务高峰)
- [ ] 通知相关团队成员
- [ ] 记录当前集群状态作为基线

#### Aurora 快照恢复演练

- [ ] 确认最新自动快照存在且状态正常
- [ ] 执行 `scripts/dr-aurora-restore.sh dev`
- [ ] 验证恢复的集群可连接
- [ ] 验证关键表数据完整性 (agents, users, sessions)
- [ ] 记录实际恢复耗时
- [ ] 确认 RTO < 15 分钟
- [ ] 清理临时恢复集群
- [ ] 填写演练报告

#### S3 版本回滚演练

- [ ] 确认 Bucket 版本控制已启用
- [ ] 执行 `scripts/dr-s3-rollback.sh ai-agents-platform-knowledge-dev`
- [ ] 验证文件内容回滚正确
- [ ] 验证删除标记恢复正确
- [ ] 清理测试文件
- [ ] 填写演练报告

#### ECS 服务重建演练

- [ ] 记录当前服务状态和任务数
- [ ] 执行强制新部署
- [ ] 监控新任务启动过程
- [ ] 验证服务健康检查通过
- [ ] 验证 ALB 流量正常转发
- [ ] 记录实际恢复耗时
- [ ] 填写演练报告

---

## 5. 监控与告警

### 5.1 现有告警 (MonitoringStack)

| 告警 | 条件 | 动作 |
|------|------|------|
| Aurora CPU 高 | CPU > 80% 连续 15 分钟 | SNS 通知 |
| Aurora 内存低 | 可用内存 < 500MB | SNS 通知 |
| Aurora 连接数高 | 连接数 > 72 (最大 80%) | SNS 通知 |
| ECS CPU 高 | CPU > 80% 连续 15 分钟 | SNS 通知 |
| ECS 内存高 | 内存 > 80% 连续 15 分钟 | SNS 通知 |
| ALB 不健康主机 | 不健康主机 >= 1 | SNS 通知 |
| ALB 5XX 错误 | 5XX > 10 次/5 分钟 | SNS 通知 |

**SNS Topic**: `ai-agents-platform-alerts-{dev|prod}`

### 5.2 灾备相关告警建议 (未来增强)

| 建议告警 | 用途 |
|---------|------|
| Aurora 备份失败 | RDS 事件订阅 |
| S3 复制延迟 | 跨区域复制场景 |
| ECS 部署失败 | 部署回滚检测 |

---

## 6. 联系人与升级流程

### 6.1 联系人列表

| 角色 | 姓名 | 联系方式 | 职责 |
|------|------|---------|------|
| 平台负责人 | (待填写) | (待填写) | 故障决策、升级审批 |
| 运维工程师 | (待填写) | (待填写) | 故障排查、恢复执行 |
| 后端开发 | (待填写) | (待填写) | 应用层问题排查 |
| AWS 支持 | - | AWS Support Console | 基础设施层问题 |

### 6.2 升级流程

```
故障发生
  ↓
CloudWatch 告警触发 → SNS 通知运维工程师
  ↓
运维工程师评估 (5 分钟内)
  ├─ 自动恢复 (ECS 任务替换等) → 监控确认恢复
  ├─ 可手动恢复 → 执行对应恢复策略
  └─ 需升级 → 通知平台负责人
       ├─ 数据层故障 → 执行 Aurora/S3 恢复
       └─ Region 级故障 → 启动跨区域恢复 (如已配置)
  ↓
恢复完成 → 记录事后报告 (Post-Mortem)
```

### 6.3 事后报告模板

每次灾备事件或演练后填写:

| 项目 | 内容 |
|------|------|
| 事件时间 | |
| 影响范围 | |
| 根因分析 | |
| 恢复步骤 | |
| 实际 RTO | |
| 实际 RPO | |
| 改进建议 | |

---

## 7. 附录

### 7.1 关键资源标识符

| 资源 | 命名模式 | 示例 |
|------|---------|------|
| Aurora 集群 | CDK 自动生成 | `ai-agents-plat-database-{env}-AuroraCluster*` |
| DB Secret | `{env}/ai-agents-platform/db-credentials` | `dev/ai-agents-platform/db-credentials` |
| S3 Bucket | `ai-agents-platform-knowledge-{env}` | `ai-agents-platform-knowledge-dev` |
| ECS 集群 | CDK 自动生成 | `ai-agents-plat-compute-{env}-Ecs*` |
| SNS Topic | `ai-agents-platform-alerts-{env}` | `ai-agents-platform-alerts-dev` |

### 7.2 验证脚本

| 脚本 | 路径 | 用途 |
|------|------|------|
| Aurora 快照恢复 | `scripts/dr-aurora-restore.sh` | 验证 Aurora 快照恢复流程 |
| S3 版本回滚 | `scripts/dr-s3-rollback.sh` | 验证 S3 版本回滚流程 |

### 7.3 相关文档

| 文档 | 说明 |
|------|------|
| `infra/lib/constructs/aurora/aurora.construct.ts` | Aurora 集群 CDK 配置 |
| `infra/lib/stacks/database-stack.ts` | 数据库 Stack (Aurora + S3) |
| `infra/lib/stacks/compute-stack.ts` | 计算 Stack (ECS Fargate) |
| `infra/lib/stacks/monitoring-stack.ts` | 监控 Stack (CloudWatch + SNS) |
| AWS Aurora PITR 文档 | https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-pitr.html |
| AWS S3 版本控制文档 | https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html |

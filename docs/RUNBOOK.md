# 运维手册 (Runbook)

> **自动生成**: 基于项目配置和现有文档
> **最后更新**: 2026-03-02

---

## 1. 服务概览

| 组件 | 技术 | 端口 | 说明 |
|------|------|------|------|
| 后端 API | FastAPI + Uvicorn | 8000 | REST API + SSE 流式通信 |
| 数据库 | MySQL 8.0 / Aurora MySQL 3.x | 3306 | 业务数据持久化 |
| 前端 | React + Vite | 3000 (dev) | SPA 应用 |
| CDK 基础设施 | AWS CDK | - | VPC / ECS / Aurora / S3 / CloudWatch |

### Stack 命名规范

```
ai-agents-plat-{stack}-{env}
```

| Stack | 包含资源 |
|-------|---------|
| `network` | VPC, Subnets, NAT Gateway |
| `security` | Security Groups, WAF, KMS |
| `database` | Aurora MySQL, S3 知识库 |
| `compute` | ECS Fargate, ALB |
| `agentcore` | Bedrock AgentCore Runtime |
| `frontend` | CloudFront, S3 静态资源托管 |
| `billing` | 计费与配额管理 |
| `monitoring` | CloudWatch Dashboard, SNS 告警 |

---

## 2. 部署流程

### 2.1 部署顺序

```
NetworkStack → SecurityStack → DatabaseStack → ComputeStack → AgentCoreStack → FrontendStack → BillingStack → MonitoringStack
```

### 2.2 CDK 部署

```bash
# 查看变更
cd infra && pnpm cdk diff --context env=<ENV>

# 部署所有 Stack
pnpm cdk deploy --all --context env=<ENV>

# 部署指定 Stack
pnpm cdk deploy ai-agents-plat-compute-<ENV> --context env=<ENV>
```

### 2.3 后端单独部署 (Docker)

```bash
# 构建镜像
cd backend && docker build -t ai-agents-platform:latest .

# ECS 强制新部署
aws ecs update-service \
  --cluster ai-agents-plat-compute-<ENV> \
  --service <SERVICE_NAME> \
  --force-new-deployment
```

### 2.4 CI/CD 自动部署

```
push to main (infra/** 变更)
  → [test] lint + typecheck + test + cdk synth
  → [deploy-dev] 自动
  → [deploy-prod] 手动审批
```

配置详见 `.github/DEPLOYMENT.md`。

---

## 3. 监控与告警

### 3.1 Health Check 端点

| 端点 | 用途 | 正常响应 |
|------|------|---------|
| `GET /health` | 存活检查 (Liveness) | `{"status": "ok"}` |
| `GET /health/ready` | 就绪检查 (Readiness) | `{"status": "ok", "checks": {...}}` |

### 3.2 CloudWatch 告警

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

### 3.3 关键指标

| 指标 | 类型 | 说明 |
|------|------|------|
| `http_requests_total` | Counter | HTTP 请求总数 |
| `http_request_duration_seconds` | Histogram | 请求延迟 |
| `db_query_duration_seconds` | Histogram | 数据库查询延迟 |
| `agent_execution_duration_seconds` | Histogram | Agent 执行耗时 |
| `llm_tokens_total` | Counter | LLM Token 消耗 |

### 3.4 日志

| 环境 | 格式 | 输出 | 级别 |
|------|------|------|------|
| Dev | 彩色控制台 | stdout | DEBUG |
| Prod | JSON | stdout → CloudWatch Logs | INFO |

**Correlation ID**: 通过 `X-Correlation-ID` Header 在请求链路中传递，structlog 自动注入。

---

## 4. 常见问题与修复

### 4.1 后端服务不可用

**症状**: Health Check 失败，API 返回 5XX

**排查步骤**:

```bash
# 1. 检查 ECS 服务状态
aws ecs describe-services \
  --cluster ai-agents-plat-compute-<ENV> \
  --services <SERVICE_NAME>

# 2. 检查任务日志
aws logs tail /ecs/ai-agents-platform-<ENV> --follow

# 3. 检查数据库连接
aws rds describe-db-clusters \
  --db-cluster-identifier <CLUSTER_ID> \
  --query 'DBClusters[0].Status'
```

**修复**:

```bash
# 方案 A: 强制新部署
aws ecs update-service \
  --cluster ai-agents-plat-compute-<ENV> \
  --service <SERVICE_NAME> \
  --force-new-deployment

# 方案 B: CDK 重新部署
cd infra && pnpm cdk deploy ai-agents-plat-compute-<ENV> --context env=<ENV>
```

### 4.2 数据库连接失败

**症状**: `OperationalError: Can't connect to MySQL server`

**排查步骤**:

```bash
# 1. 检查 Aurora 集群状态
aws rds describe-db-clusters --query 'DBClusters[].{ID:DBClusterIdentifier,Status:Status}'

# 2. 检查 Security Group 是否允许入站
aws ec2 describe-security-groups --group-ids <SG_ID>

# 3. 检查 Secrets Manager 凭证
aws secretsmanager get-secret-value --secret-id <ENV>/ai-agents-platform/db-credentials
```

**修复**:
- Security Group 问题: 通过 CDK 修复后重新部署 `SecurityStack`
- 凭证过期: 轮换 Secrets Manager 中的密钥

### 4.3 Agent 执行超时

**症状**: Agent 调用无响应或返回超时

**排查步骤**:

```bash
# 1. 检查 AgentCore Runtime 状态
aws bedrock-agent list-agents --query 'agentSummaries[].{Name:agentName,Status:agentStatus}'

# 2. 检查日志中的 agent.execute span
aws logs filter-log-events \
  --log-group-name /ecs/ai-agents-platform-<ENV> \
  --filter-pattern '"agent.execute"'
```

### 4.4 本地开发常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `uv: command not found` | uv 未安装 | `pip install uv` |
| MySQL 连接被拒 | Docker 未启动 | `docker run -d --name mysql-dev -p 3306:3306 -e MYSQL_ROOT_PASSWORD=changeme -e MYSQL_DATABASE=ai_agents_platform mysql:8.0` |
| `ModuleNotFoundError` | 依赖未安装 | `cd backend && uv sync` |
| TypeScript 类型错误 | 依赖过期 | `pnpm install` |
| CDK synth 失败 | Context 缓存过期 | 删除 `cdk.context.json` 后重试 |

---

## 5. 回滚流程

### 5.1 后端回滚

```bash
# 查看部署历史
aws ecs describe-services \
  --cluster ai-agents-plat-compute-<ENV> \
  --services <SERVICE_NAME> \
  --query 'services[0].deployments'

# 回滚到上一版本任务定义
aws ecs update-service \
  --cluster ai-agents-plat-compute-<ENV> \
  --service <SERVICE_NAME> \
  --task-definition <PREVIOUS_TASK_DEFINITION_ARN>
```

### 5.2 CDK 回滚

```bash
# CDK 自动回滚 (CloudFormation 级)
pnpm cdk deploy --all --context env=<ENV> --rollback

# 紧急: 销毁并重建单个 Stack
pnpm cdk destroy ai-agents-plat-compute-<ENV>
pnpm cdk deploy ai-agents-plat-compute-<ENV> --context env=<ENV>
```

### 5.3 数据库回滚

详见 `docs/disaster-recovery-plan.md`。

**快速参考**:

| 场景 | 恢复策略 | RPO | 脚本 |
|------|---------|-----|------|
| 数据误删/逻辑错误 | Aurora PITR (时间点恢复) | ≈ 0 (秒级) | 手动 |
| 集群损坏 | Aurora 快照恢复 | = 最近快照 | `scripts/dr-aurora-restore.sh` |
| S3 文件误删 | S3 版本回滚 | ≈ 0 | `scripts/dr-s3-rollback.sh` |

---

## 6. 环境配置

### 6.1 环境矩阵

| 配置 | Dev | Prod |
|------|-----|------|
| ECS 实例 | 256 CPU / 512 MiB / 1 任务 | 512 CPU / 1024 MiB / 2 任务 |
| Aurora | db.t3.medium 单实例 | db.r6g.large 多 AZ |
| NAT Gateway | 1 | 每 AZ 一个 |
| S3 加密 | S3 Managed | CMK (KMS) |
| Aurora 备份保留 | 7 天 | 30 天 |
| CloudWatch 日志保留 | 1 周 | 1 年 |
| RemovalPolicy | DESTROY | RETAIN / SNAPSHOT |

### 6.2 关键资源标识符

| 资源 | 命名模式 |
|------|---------|
| Aurora 集群 | `ai-agents-plat-database-{env}-AuroraCluster*` |
| DB Secret | `{env}/ai-agents-platform/db-credentials` |
| S3 Bucket | `ai-agents-platform-knowledge-{env}` |
| ECS 集群 | `ai-agents-plat-compute-{env}-Ecs*` |
| SNS Topic | `ai-agents-platform-alerts-{env}` |

### 6.3 成本标签

所有资源必须标记:

```
Project: ai-agents-platform
Environment: dev | prod
CostCenter: ai-platform
ManagedBy: cdk
```

---

## 7. 灾备恢复

### 7.1 恢复目标

| 指标 | 目标 | 说明 |
|------|------|------|
| RPO | < 5 分钟 | 最多丢失最近 5 分钟数据 |
| RTO | < 15 分钟 | 从故障到服务恢复 |

### 7.2 验证脚本

| 脚本 | 路径 | 用途 |
|------|------|------|
| Aurora 快照恢复 | `scripts/dr-aurora-restore.sh` | 验证 Aurora 快照恢复 |
| S3 版本回滚 | `scripts/dr-s3-rollback.sh` | 验证 S3 版本回滚 |

### 7.3 演练计划

季度演练: Aurora PITR / 快照恢复, S3 回滚
半年演练: ECS 服务重建

详见 `docs/disaster-recovery-plan.md`。

---

## 8. 压测

### 8.1 工具

Locust — 位于 `scripts/loadtest/`

### 8.2 运行

```bash
cd scripts/loadtest
pip install -r requirements.txt
bash run.sh
```

结果输出到 `scripts/loadtest/results/`。

### 8.3 性能基线

详见 `docs/performance-baseline.md`。

---

## 相关文档

| 文档 | 说明 |
|------|------|
| `docs/CONTRIB.md` | 开发贡献指南 |
| `docs/disaster-recovery-plan.md` | 完整灾备方案 |
| `docs/performance-baseline.md` | 性能基线 |
| `.github/DEPLOYMENT.md` | CI/CD 部署配置 |
| `docs/rollout-plan.md` | 推广计划 |

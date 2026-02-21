# 灾备恢复运维手册 (Disaster Recovery Runbook)

> AI Agents Platform 灾备恢复流程、验证方法和演练计划

---

## 1. 灾备目标

| 指标 | 目标值 | 实现方式 |
|------|--------|---------|
| **RPO** (恢复点目标) | < 5 分钟 | Aurora 持续备份 + S3 版本管理 |
| **RTO** (恢复时间目标) | < 15 分钟 | 预置恢复脚本 + 自动化流程 |

### 数据保护层级

| 数据源 | 备份策略 | RPO | 保留期 |
|--------|---------|-----|--------|
| Aurora MySQL (Dev) | 自动备份 + 持续备份 | ~5 分钟 | 7 天 |
| Aurora MySQL (Prod) | 自动备份 + 持续备份 | ~5 分钟 | 30 天 |
| S3 知识库文档 | 版本控制 | 0 (每次写入即备份) | 当前版本 + 30 天旧版本 |
| Secrets Manager | 自动复制 | 0 | 按策略 |

---

## 2. RPO 验证方法

### 2.1 Aurora 持续备份验证

Aurora MySQL 自动备份默认提供 5 分钟粒度的恢复能力。

**验证步骤:**

```bash
# 1. 检查备份保留期配置
aws rds describe-db-clusters \
  --db-cluster-identifier ai-agents-platform-db-<env> \
  --query 'DBClusters[0].BackupRetentionPeriod'
# 预期: Dev=7, Prod=30

# 2. 查看最新自动快照
aws rds describe-db-cluster-snapshots \
  --db-cluster-identifier ai-agents-platform-db-<env> \
  --snapshot-type automated \
  --query 'DBClusterSnapshots | sort_by(@, &SnapshotCreateTime) | [-1].{ID:DBClusterSnapshotIdentifier,Time:SnapshotCreateTime,Status:Status}'

# 3. 计算 RPO (快照时间 vs 当前时间)
# 自动快照间隔约为 5 分钟，加上事务日志可精确到秒级恢复
```

**验证标准:**
- [ ] 备份保留期符合要求 (Dev: 7天, Prod: 30天)
- [ ] 最新快照时间距当前时间 < 24 小时 (自动备份每日触发)
- [ ] 快照状态为 `available`
- [ ] 持续备份已启用 (Aurora 默认启用)

### 2.2 S3 版本管理验证

```bash
# 1. 检查版本控制状态
aws s3api get-bucket-versioning \
  --bucket ai-agents-platform-knowledge-<env>
# 预期: {"Status": "Enabled"}

# 2. 检查生命周期规则
aws s3api get-bucket-lifecycle-configuration \
  --bucket ai-agents-platform-knowledge-<env>
# 预期: 旧版本 30 天过期

# 3. 验证版本可恢复性 (测试文件)
aws s3api list-object-versions \
  --bucket ai-agents-platform-knowledge-<env> \
  --prefix "test-file.txt" \
  --max-keys 5
```

**验证标准:**
- [ ] 版本控制状态为 `Enabled`
- [ ] 旧版本过期策略配置正确 (30天)
- [ ] 可列出对象的历史版本
- [ ] 可恢复到指定版本

---

## 3. RTO 恢复流程 Checklist

### 3.1 Aurora 集群恢复 (预计 10-12 分钟)

**前提:** 确认故障类型 (数据损坏 / 集群不可用 / 误操作)

| 步骤 | 操作 | 预计时间 | 负责人 |
|------|------|---------|--------|
| 1 | 确认故障范围和影响 | 1 分钟 | 值班工程师 |
| 2 | 通知相关人员 | 1 分钟 | 值班工程师 |
| 3 | 执行恢复脚本 | 8-10 分钟 | DBA / 平台工程师 |
| 4 | 验证数据完整性 | 2 分钟 | DBA |
| 5 | 切换应用连接 | 2 分钟 | 平台工程师 |
| 6 | 验证应用正常 | 1 分钟 | 值班工程师 |

**恢复命令:**

```bash
# 使用恢复脚本 (推荐)
./infra/scripts/aurora-restore.sh --env <dev|prod>

# 或指定特定快照
./infra/scripts/aurora-restore.sh --env prod --snapshot-id <snapshot-id>

# 仅查看恢复计划
./infra/scripts/aurora-restore.sh --env prod --dry-run
```

**恢复后验证:**

```bash
# 1. 检查集群状态
aws rds describe-db-clusters \
  --db-cluster-identifier <new-cluster-id> \
  --query 'DBClusters[0].Status'
# 预期: "available"

# 2. 测试数据库连接
mysql -h <new-endpoint> -P 3306 -u admin -p \
  -e "SELECT COUNT(*) FROM ai_agents_platform.agents;"

# 3. 验证关键表数据
mysql -h <new-endpoint> -P 3306 -u admin -p \
  -e "SELECT MAX(updated_at) FROM ai_agents_platform.agents;"
```

### 3.2 S3 知识库恢复 (预计 5-10 分钟)

| 步骤 | 操作 | 预计时间 | 负责人 |
|------|------|---------|--------|
| 1 | 确认受影响的文件范围 | 1 分钟 | 值班工程师 |
| 2 | 确定回滚目标日期 | 1 分钟 | 产品/工程 |
| 3 | 执行回滚脚本 (dry-run) | 1 分钟 | 平台工程师 |
| 4 | 确认回滚计划 | 1 分钟 | 平台工程师 |
| 5 | 执行实际回滚 | 3-5 分钟 | 平台工程师 |
| 6 | 验证回滚完整性 | 2 分钟 | 平台工程师 |

**恢复命令:**

```bash
# 先预览回滚计划
./infra/scripts/s3-rollback.sh --env <dev|prod> --target-date 2025-01-15 --dry-run

# 执行回滚
./infra/scripts/s3-rollback.sh --env <dev|prod> --target-date 2025-01-15

# 仅回滚特定前缀
./infra/scripts/s3-rollback.sh --env prod --target-date 2025-01-15 --prefix "documents/"
```

### 3.3 全栈恢复 (预计 15 分钟)

当需要同时恢复数据库和 S3 时:

1. **并行启动** Aurora 恢复和 S3 回滚 (可由两人同时操作)
2. Aurora 恢复完成后，更新应用配置指向新端点
3. 重启应用服务
4. 执行端到端验证

---

## 4. 脚本使用说明

### 4.1 aurora-restore.sh

**功能:** 从最新自动备份恢复 Aurora MySQL 集群

**参数:**

| 参数 | 必需 | 说明 |
|------|:----:|------|
| `--env <dev\|prod>` | 是 | 目标环境 |
| `--snapshot-id <id>` | 否 | 指定快照 ID (默认最新) |
| `--new-cluster-id <id>` | 否 | 新集群标识符 |
| `--skip-dns` | 否 | 跳过 DNS 切换提示 |
| `--dry-run` | 否 | 仅显示计划 |

**安全机制:**
- Prod 环境需输入 `RESTORE-PROD` 确认
- Dev 环境需输入 `y` 确认
- `--dry-run` 模式不执行任何变更
- 自动记录 RPO (快照时间 vs 当前时间)

### 4.2 s3-rollback.sh

**功能:** 将 S3 Bucket 对象批量回滚到指定日期的版本

**参数:**

| 参数 | 必需 | 说明 |
|------|:----:|------|
| `--env <dev\|prod>` | 是 | 目标环境 |
| `--target-date <YYYY-MM-DD>` | 是 | 回滚目标日期 |
| `--bucket-name <name>` | 否 | Bucket 名称 (默认自动推导) |
| `--prefix <prefix>` | 否 | 仅回滚指定前缀 |
| `--dry-run` | 否 | 仅显示计划 |
| `--batch-size <n>` | 否 | 每批大小 (默认 100) |

**安全机制:**
- Prod 环境需输入 `ROLLBACK-PROD` 确认
- `--dry-run` 模式仅列出受影响对象
- 回滚后自动验证完整性
- 不会删除目标日期之前的版本

---

## 5. 定期演练计划

### 5.1 演练频率

| 演练类型 | 频率 | 环境 | 参与人 |
|---------|------|------|--------|
| Aurora 快照恢复 | 每季度 | Dev | DBA + 平台工程师 |
| S3 版本回滚 | 每季度 | Dev | 平台工程师 |
| 全栈恢复 | 每半年 | Dev | 全团队 |
| Prod 恢复验证 | 每年 | Prod (只读验证) | DBA + 平台工程师 + 管理层 |

### 5.2 季度演练 Checklist

**演练前准备:**
- [ ] 通知相关团队演练时间
- [ ] 确认 Dev 环境可用
- [ ] 准备测试数据 (在 Dev 环境插入标记数据)
- [ ] 记录演练前的集群状态和数据快照

**Aurora 恢复演练:**
- [ ] 在 Dev 数据库中插入标记数据 (如 `INSERT INTO test_table VALUES ('drill-YYYYMMDD')`)
- [ ] 等待自动备份完成 (或手动创建快照)
- [ ] 执行 `aurora-restore.sh --env dev`
- [ ] 验证恢复后的集群包含标记数据
- [ ] 记录实际恢复时间 (对比 RTO 目标)
- [ ] 清理恢复的测试集群

**S3 回滚演练:**
- [ ] 在 Dev 知识库 Bucket 上传标记文件
- [ ] 记录上传前的时间点
- [ ] 执行 `s3-rollback.sh --env dev --target-date <上传前日期> --dry-run`
- [ ] 确认 dry-run 结果正确
- [ ] 执行实际回滚
- [ ] 验证标记文件已回滚
- [ ] 记录实际回滚时间

**演练后总结:**
- [ ] 记录实际 RTO (是否满足 < 15 分钟)
- [ ] 记录发现的问题和改进项
- [ ] 更新本 Runbook (如有流程变更)
- [ ] 归档演练报告

### 5.3 演练报告模板

```
## 灾备演练报告 - YYYY-MM-DD

### 基本信息
- 演练类型: [Aurora恢复 / S3回滚 / 全栈恢复]
- 演练环境: [Dev / Prod只读]
- 参与人员: [名单]

### 演练结果
- RPO 实际值: [X 分钟] (目标: < 5 分钟)
- RTO 实际值: [X 分钟] (目标: < 15 分钟)
- 结果: [通过 / 未通过]

### 发现的问题
1. [问题描述] -> [改进措施]

### 改进计划
1. [计划项] -> [负责人] -> [截止日期]
```

---

## 6. 故障场景与应对

### 场景 A: Aurora 集群不可用

**症状:** 应用无法连接数据库，RDS 控制台显示集群异常

**应对:**
1. 确认是否为暂时性网络问题 (重试连接)
2. 检查 RDS 事件日志: `aws rds describe-events --source-type db-cluster`
3. 如集群确实不可用，执行 Aurora 恢复流程 (3.1)

### 场景 B: 数据被误删/损坏

**症状:** 应用数据异常，疑似误操作导致

**应对:**
1. 立即停止应用写入 (如有可能)
2. 确定数据损坏的时间点
3. 使用 Point-in-Time Recovery 恢复到损坏前:
   ```bash
   aws rds restore-db-cluster-to-point-in-time \
     --source-db-cluster-identifier ai-agents-platform-db-<env> \
     --db-cluster-identifier <new-cluster-id> \
     --restore-to-time <损坏前时间ISO格式>
   ```
4. 验证恢复数据并切换连接

### 场景 C: S3 文件被误删

**症状:** 知识库文档丢失或内容被篡改

**应对:**
1. 确定受影响文件的范围和时间
2. 执行 S3 回滚流程 (3.2)
3. 如仅个别文件，可直接恢复特定版本:
   ```bash
   aws s3api get-object \
     --bucket ai-agents-platform-knowledge-<env> \
     --key <file-key> \
     --version-id <target-version-id> \
     <output-file>
   ```

### 场景 D: 整个区域不可用

**症状:** AWS 区域级故障

**应对:**
1. 当前架构为单区域部署 (ap-northeast-1)
2. 等待 AWS 恢复区域服务
3. 如需跨区域灾备，参考后续架构演进计划

---

## 7. 联系人与升级流程

| 级别 | 触发条件 | 通知对象 | 响应时间 |
|------|---------|---------|---------|
| P1 | Prod 数据库不可用 | DBA + 平台工程师 + 技术负责人 | 5 分钟 |
| P2 | Prod 数据损坏/误删 | DBA + 平台工程师 | 15 分钟 |
| P3 | Dev 环境故障 | 平台工程师 | 1 小时 |
| P4 | S3 文件异常 (非紧急) | 平台工程师 | 4 小时 |

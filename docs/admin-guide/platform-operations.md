# 平台运维

> 本指南说明平台日常运维操作，包括监控告警、成本管理、工具审批和灾备恢复。

---

## 目录

- [运维概览](#运维概览)
- [监控告警](#监控告警)
- [成本管理](#成本管理)
- [工具审批流程](#工具审批流程)
- [灾备恢复](#灾备恢复)
- [日常运维检查清单](#日常运维检查清单)
- [API 参考](#api-参考)
- [常见问题](#常见问题)

---

## 运维概览

### 基础设施组件

| 组件 | 服务 | 监控方式 |
|------|------|---------|
| 应用服务 | ECS Fargate | CloudWatch Alarms |
| 数据库 | Aurora MySQL | CloudWatch Metrics + Performance Insights |
| 负载均衡 | ALB | CloudWatch Target Health |
| AI 服务 | Bedrock | CloudWatch Invocation Metrics |
| 知识库存储 | S3 | S3 Metrics |
| 日志 | CloudWatch Logs | Log Insights |

### 健康检查端点

| 端点 | 说明 | 检查内容 |
|------|------|---------|
| `GET /health` | 存活检查 (Liveness) | 应用进程运行状态 |
| `GET /health/ready` | 就绪检查 (Readiness) | 数据库连接 + 依赖服务 |

**就绪检查响应示例**:

```json
{
  "status": "ok",
  "checks": {
    "database": "ok"
  }
}
```

当数据库不可用时:

```json
{
  "status": "degraded",
  "checks": {
    "database": "error"
  }
}
```

ALB 使用就绪检查端点判断 ECS 任务是否可接收流量。

---

## 监控告警

### CloudWatch Alarms

平台配置了以下核心告警:

| 告警名称 | 触发条件 | 严重级别 | 建议操作 |
|---------|---------|---------|---------|
| ECS CPU 高 | CPU > 80% 持续 5 分钟 | 警告 | 检查是否需要扩容 |
| ECS 内存高 | 内存 > 80% 持续 5 分钟 | 警告 | 检查内存泄漏 |
| ALB 5xx 错误 | 5xx > 10 次/分钟 | 严重 | 检查应用日志 |
| Aurora CPU 高 | CPU > 70% 持续 10 分钟 | 警告 | 检查慢查询 |
| Aurora 连接数高 | 连接数 > 80% | 警告 | 检查连接池配置 |

### CloudWatch Dashboard

Prod 环境提供统一监控仪表板，包含:

- ECS 任务 CPU/内存使用率
- ALB 请求量和错误率
- Aurora 数据库性能指标
- Bedrock 调用量和延迟

### SNS 告警通知

告警通过 SNS 发送通知。配置告警接收人:

1. 登录 AWS Console
2. 进入 SNS 服务
3. 找到平台告警 Topic
4. 添加订阅（邮箱或 Slack Webhook）

---

## 成本管理

### Insights 仪表板

平台内置 Insights 功能帮助管理员监控使用量和成本:

#### 概览统计

```
GET /api/v1/insights/summary?start_date=2026-02-01&end_date=2026-02-14
```

返回:

```json
{
  "total_agents": 25,
  "active_agents": 18,
  "total_invocations": 1500,
  "total_cost": 45.67,
  "total_tokens": 2500000,
  "period": {
    "start_date": "2026-02-01",
    "end_date": "2026-02-14"
  }
}
```

| 指标 | 说明 | 数据来源 |
|------|------|---------|
| total_agents | 总 Agent 数量 | 平台数据库 |
| active_agents | 活跃 Agent 数量 | 平台数据库 |
| total_invocations | 总调用次数 | 使用记录表 |
| total_cost | 总成本 (USD) | AWS Cost Explorer (真实账单) |
| total_tokens | 总 Token 消耗 | 使用记录表 |

#### 按 Agent 的成本归因

```
GET /api/v1/insights/cost-breakdown?start_date=2026-02-01&end_date=2026-02-14
```

返回每个 Agent 的 Token 消耗明细:

```json
{
  "items": [
    {
      "agent_id": 1,
      "agent_name": "客服助手",
      "total_tokens": 500000,
      "tokens_input": 200000,
      "tokens_output": 300000,
      "invocation_count": 350
    }
  ],
  "total_tokens": 2500000,
  "period": { "start_date": "2026-02-01", "end_date": "2026-02-14" }
}
```

#### 使用趋势

```
GET /api/v1/insights/usage-trends?start_date=2026-02-01&end_date=2026-02-14
```

返回按日的使用趋势数据，适合生成图表:

```json
{
  "data_points": [
    {
      "date": "2026-02-01",
      "invocation_count": 120,
      "total_tokens": 180000,
      "unique_users": 15
    }
  ]
}
```

### 成本优化策略

#### Dev 环境定时缩减

Dev 环境配置了 ECS Scheduled Scaling，非工作时段自动缩减:

| 时间 (UTC) | 操作 | 节省 |
|------------|------|------|
| 12:00 (北京时间 20:00) | 缩减到 0 任务 | 约 50% Dev 环境成本 |
| 00:00 (北京时间 08:00) | 恢复到 1 任务 | - |

#### 模型使用建议

| 场景 | 推荐模型 | 成本控制 |
|------|---------|---------|
| 简单问答 | Haiku | 最低成本 |
| 代码生成 | Sonnet | 平衡选择 |
| 复杂推理 | Opus | 仅必要时使用 |

建议通过 Insights 定期分析各 Agent 的模型使用情况，将非必要使用 Opus/Sonnet 的 Agent 调整为 Haiku。

---

## 工具审批流程

ADMIN 负责审核 DEVELOPER 提交的工具注册申请。

### 审批操作

#### 查看待审批工具

```
GET /api/v1/tools?status=pending_review
```

#### 审批通过

确认工具配置安全且符合规范后:

```
POST /api/v1/tools/{tool_id}/approve
Authorization: Bearer <admin_token>
```

审批通过后:

- 工具状态变为 APPROVED
- 工具自动同步到 AgentCore Gateway
- 所有 Agent 可以关联和使用该工具

#### 审批拒绝

发现安全问题或配置不当时:

```
POST /api/v1/tools/{tool_id}/reject
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "comment": "API 端点缺少认证配置，请添加 auth_type 和认证凭证"
}
```

拒绝后:

- 工具状态变为 REJECTED
- 创建者可查看拒绝原因
- 创建者修改后可重新提交

### 审批检查清单

审批工具时建议检查以下项目:

- [ ] 工具描述清晰，功能明确
- [ ] endpoint_url/server_url 指向可信任的内部或认证服务
- [ ] 配置了适当的认证方式 (auth_type)
- [ ] 没有暴露敏感信息
- [ ] 工具权限范围合理（不会过度授权）
- [ ] 已与工具创建者确认使用场景

#### 废弃工具

不再需要的已批准工具可以废弃:

```
POST /api/v1/tools/{tool_id}/deprecate
```

废弃操作不可逆。废弃后工具从 Gateway 移除。

---

## 灾备恢复

### 灾备指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| RPO | < 5 分钟 | 恢复点目标: 最多丢失 5 分钟数据 |
| RTO | < 15 分钟 | 恢复时间目标: 15 分钟内恢复服务 |

### Aurora 数据库恢复

**自动备份**: Aurora 持续备份到 S3，保留期 7 天。Prod 环境启用 Performance Insights。

**恢复流程**:

1. 确认故障范围和数据丢失时间点
2. 在 AWS Console 中选择 Aurora 快照或指定时间点
3. 执行恢复脚本: `scripts/disaster-recovery/aurora-snapshot-restore.sh`
4. 更新 ECS 任务的数据库连接配置
5. 验证数据完整性

### S3 文档恢复

知识库文档存储在 S3，已启用版本管理。

**恢复流程**:

1. 确认需要恢复的文件和版本
2. 执行回滚脚本: `scripts/disaster-recovery/s3-version-rollback.sh`
3. 触发知识库同步以更新索引

### ECS 服务恢复

ECS 任务故障时:

1. 检查 ECS 任务停止原因（CloudWatch Logs）
2. 如果是 OOM，考虑调整内存配置
3. 如果是应用错误，回滚到上一个稳定版本
4. ECS 会自动重启失败的任务

---

## 日常运维检查清单

### 每日检查

- [ ] 检查 `/health/ready` 端点返回 `"status": "ok"`
- [ ] 查看 CloudWatch Dashboard 确认无告警
- [ ] 检查待审批工具数量（`GET /tools?status=pending_review`）

### 每周检查

- [ ] 查看 Insights 成本趋势，确认无异常增长
- [ ] 审查审计日志中的异常操作（频繁失败登录、大量删除等）
- [ ] 确认 Aurora 自动备份正常

### 每月检查

- [ ] 审查用户角色分配是否合理
- [ ] 分析 Token 使用量，优化高消耗 Agent 的模型选择
- [ ] 检查 S3 存储量增长趋势
- [ ] 确认 ECS 任务无内存泄漏（内存使用率是否持续增长）

---

## API 参考

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 存活检查 |
| GET | `/health/ready` | 就绪检查 |

### Insights 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/insights/summary` | 概览统计 |
| GET | `/api/v1/insights/cost-breakdown` | 按 Agent 成本归因 |
| GET | `/api/v1/insights/usage-trends` | 使用趋势 |
| GET | `/api/v1/insights/usage-records` | 使用记录列表 |
| GET | `/api/v1/insights/usage-records/{id}` | 使用记录详情 |
| GET | `/api/v1/insights/usage-summary` | 使用量摘要 (旧接口) |

### Insights 查询参数

| 参数 | 说明 | 适用端点 |
|------|------|---------|
| start_date | 开始日期 (ISO 8601) | summary, cost-breakdown, usage-trends |
| end_date | 结束日期 (ISO 8601) | summary, cost-breakdown, usage-trends |
| user_id | 用户 ID 筛选 | usage-records (ADMIN 可指定) |
| agent_id | Agent ID 筛选 | usage-records |

---

## 常见问题

### Q1: CloudWatch Alarm 频繁触发怎么办？

1. **CPU 告警**: 检查是否有大量并发请求或复杂的 Agent Teams 任务。考虑调整 ECS 任务规格或增加任务数量。
2. **内存告警**: 检查是否有 SSE 长连接堆积。确认 SSE 连接管理器的并发限制配置。
3. **5xx 告警**: 查看 ECS 日志定位具体错误。常见原因包括数据库连接超时和 Bedrock API 限流。

### Q2: 如何估算月度成本？

使用 Insights 的使用趋势数据推算:

1. 查看最近 7 天的日均 Token 消耗
2. 乘以 30 估算月度 Token 消耗
3. 参照 Bedrock 定价计算 LLM 成本
4. 加上基础设施成本 (ECS + Aurora + S3 + 数据传输)

建议同时查看 AWS Cost Explorer 获取精确账单。

### Q3: 工具审批应该关注哪些安全风险？

重点关注:

1. **端点安全**: 确认 endpoint_url 指向内部或已认证的服务
2. **认证配置**: API 类型工具必须配置认证方式
3. **权限范围**: 工具不应有过度的数据访问权限
4. **数据泄露**: 确认工具不会将敏感数据发送到外部

### Q4: Dev 环境定时缩减后如何手动恢复？

如果在非工作时段需要使用 Dev 环境:

1. 登录 AWS Console > ECS
2. 找到 Dev 环境的 Service
3. 将 Desired Count 手动调整为 1
4. 等待任务启动（约 2-3 分钟）

注意: 下次定时缩减时间到达后会自动缩回 0。

### Q5: 如何处理 Bedrock API 限流？

Bedrock API 有调用频率限制。当出现限流时:

1. 检查 Insights 确认调用量是否异常
2. 优化高频调用的 Agent（减少不必要的 API 调用）
3. 考虑在 Agent 配置中使用 Haiku 替代 Sonnet/Opus（Haiku 限流阈值更高）
4. 如持续限流，联系 AWS 申请提升配额

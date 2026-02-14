# AI Agents Platform 管理员手册

> 版本: 1.0 | 更新日期: 2026-02-14 | 适用角色: ADMIN

---

## 目录

- [管理员职责](#管理员职责)
- [ADMIN 专属功能](#admin-专属功能)
- [快速导航](#快速导航)
- [系统架构概览](#系统架构概览)
- [常见问题](#常见问题)

---

## 管理员职责

ADMIN 角色是平台的最高权限角色，负责以下核心职责:

1. **用户管理**: 创建和管理用户账户，分配角色
2. **工具审批**: 审核 DEVELOPER 提交的工具注册申请
3. **安全监控**: 通过审计日志追踪平台操作
4. **成本管理**: 通过 Insights 仪表板监控全局成本
5. **平台运维**: 监控告警、灾备恢复

---

## ADMIN 专属功能

以下功能仅 ADMIN 角色可访问:

| 功能 | 说明 | 入口 |
|------|------|------|
| 审计日志查看 | 查看全平台操作记录 | 左侧导航 > 审计日志 |
| 审计日志导出 | 导出 CSV 文件 | 审计日志 > 导出 |
| 工具审批 | 批准或拒绝工具注册 | 工具目录 > 待审批 |
| 全局 Insights | 查看所有用户的使用数据 | 使用洞察 |
| 用户管理 | 管理用户角色和状态 | (API 操作) |

### ADMIN 增强权限

以下功能所有角色可用，但 ADMIN 有额外权限:

| 功能 | 普通用户 | ADMIN |
|------|---------|-------|
| Agent 管理 | 仅自己的 | 所有用户的 |
| 使用洞察 | 仅自己的数据 | 全局数据 |
| 工具废弃 | 仅自己创建的 | 所有工具 |

---

## 快速导航

| 管理任务 | 请阅读 |
|---------|--------|
| 管理用户账户和角色 | [用户管理](user-management.md) |
| 日常运维和成本监控 | [平台运维](platform-operations.md) |

### 用户手册参考

管理员同时具备普通用户的所有能力。功能使用指南请参阅:

- [快速入门](../user-guide/quick-start.md)
- [Agent 管理指南](../user-guide/agent-management.md)
- [工具集成指南](../user-guide/tool-integration.md)
- [知识库使用指南](../user-guide/knowledge-base.md)
- [模板使用指南](../user-guide/templates.md)

---

## 系统架构概览

平台采用分层架构，管理员需了解以下关键组件:

### 后端服务

- **运行环境**: AWS ECS Fargate
- **Web 框架**: Python FastAPI
- **数据库**: Aurora MySQL 3.x (Writer + Reader)
- **AI 引擎**: Amazon Bedrock (Claude 系列模型)
- **Agent 运行时**: Bedrock AgentCore Runtime

### 环境配置

| 维度 | Dev 环境 | Prod 环境 |
|------|---------|----------|
| ECS | 256 CPU / 512 MiB / 1 任务 | 512 CPU / 1024 MiB / 2 任务 |
| Aurora | db.t3.medium (1 实例) | db.r6g.large (Writer + Reader) |
| 监控 | CloudWatch Alarms | CloudWatch Alarms + Dashboard |
| 成本优化 | 定时缩减 (非工作时段) | 始终运行 |

### 关键 API 前缀

所有 API 端点以 `/api/v1/` 为前缀，共 66+ 端点:

| 模块 | 前缀 | 端点数 |
|------|------|:------:|
| 认证 | `/api/v1/auth/` | 5 |
| Agent | `/api/v1/agents/` | 8 |
| 对话 | `/api/v1/conversations/` | 6 |
| 团队执行 | `/api/v1/team-executions/` | 6 |
| 工具目录 | `/api/v1/tools/` | 10 |
| 知识库 | `/api/v1/knowledge-bases/` | 10 |
| 模板 | `/api/v1/templates/` | 8 |
| 使用洞察 | `/api/v1/insights/` | 6 |
| 评估 | `/api/v1/test-suites/` + `/api/v1/evaluation-runs/` | 14 |
| 审计日志 | `/api/v1/audit-logs/` | 5 |
| 健康检查 | `/health`, `/health/ready` | 2 |

---

## 常见问题

### Q1: 如何获取 ADMIN 权限？

ADMIN 权限需要在数据库层面或通过现有 ADMIN 账户分配。平台初始部署时会创建默认 ADMIN 账户。

### Q2: ADMIN 操作会被审计吗？

是的。所有操作（包括 ADMIN 的操作）都会记录在审计日志中。这包括 API 调用、资源变更和登录行为。

### Q3: 平台出现故障如何排查？

1. 检查 `/health/ready` 端点确认服务健康状态
2. 查看 CloudWatch Alarms 确认是否有告警
3. 检查审计日志中的最近操作
4. 查看 ECS 任务日志定位错误

详细运维流程请参阅 [平台运维](platform-operations.md)。

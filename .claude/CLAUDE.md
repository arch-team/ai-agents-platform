# AI Agents Platform - Monorepo

## 响应语言
**所有对话和文档必须（Must）使用中文。**
**除非有特殊说明，请用中文回答。** (Unless otherwise specified, please respond in Chinese.)

### 强制要求

- 所有对话必须使用中文
- 代码注释使用中文
- 文档内容使用中文
- Git 提交信息使用中文

### 例外情况

以下内容保持英文:
- 代码变量名、函数名、类名
- 技术术语 (如 API, SDK, TDD)
- 第三方库/框架名称
- 错误信息和日志 (可选)

---

## 项目概述

AI Agents Platform — 基于 Amazon Bedrock AgentCore 的企业级 AI Agents 平台。

- **架构**: DDD + Modular Monolith + Clean Architecture
- **技术栈**: Python 3.11+ / FastAPI / SQLAlchemy 2.0+ / Aurora MySQL
- **北极星指标**: 周活跃 Agent 数量 (WAA)

---

## 会话协议

> **每次会话开始时必须阅读 [docs/progress.md](../docs/progress.md)**，了解当前进度和上次会话产出。
> 会话结束前更新 `docs/progress.md` 的"当前状态"和"上次会话"。

---

## Git 分支

```
feat/{module-name} → main
```

功能分支直接从 main 创建，完成后合并回 main。提交规范见 `.claude/rules/common.md`。

---

## Monorepo 结构

| 子项目 | 路径 | 说明 |
|--------|------|------|
| 后端服务 | `backend/` | Python + FastAPI |
| 前端应用 | `frontend/` | (计划中) |
| 基础设施 | `infra/` | (计划中) |

进入子目录后，Claude Code 自动加载该子项目的规范：

```bash
cd backend/   # 加载 backend/.claude/CLAUDE.md
cd frontend/  # 加载 frontend/.claude/CLAUDE.md
cd infra/     # 加载 infra/.claude/CLAUDE.md
```

---

## 相关文档

| 子项目 | 规范文档 |
|--------|---------|
| 后端 | [backend/.claude/CLAUDE.md](../backend/.claude/CLAUDE.md) |
| 通用规则 | [.claude/rules/common.md](.claude/rules/common.md) |

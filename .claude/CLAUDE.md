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

AI Agents Platform - 基于 Amazon Bedrock AgentCore 的企业级 AI Agents 平台。

## Monorepo 结构

| 子项目 | 路径 | 说明 |
|--------|------|------|
| 后端服务 | `backend/` | Python + FastAPI |
| 前端应用 | `frontend/` | (计划中) |
| 基础设施 | `infra/` | (计划中) |

## 开发指南

进入对应子目录后，Claude Code 会自动加载该子项目的规范：

```bash
cd backend/   # 加载后端规范
cd frontend/  # 加载前端规范
cd infra/     # 加载基础设施规范
```

## 相关文档

| 子项目 | 规范文档 |
|--------|---------|
| 后端 | [backend/.claude/CLAUDE.md](backend/.claude/CLAUDE.md) |
| 通用规则 | [.claude/rules/common.md](.claude/rules/common.md) |

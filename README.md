# AI Agents Platform

基于 Amazon Bedrock AgentCore 的企业级 AI Agents 平台。

## 项目结构

```
ai-agents-platform/
├── backend/    # 后端服务 (Python + FastAPI)
├── frontend/   # 前端应用 (计划中)
├── infra/      # 基础设施 (计划中)
└── doc/        # 项目文档
```

## 快速开始

### 后端开发

```bash
cd backend
uv sync
uv run uvicorn src.presentation.api.main:app --reload
```

## 文档

- [后端开发规范](backend/.claude/CLAUDE.md)
- [通用规范](.claude/CLAUDE.md)

## 贡献指南

请参考各子项目的 `.claude/` 目录中的规范文档。

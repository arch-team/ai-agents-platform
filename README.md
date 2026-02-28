# AI Agents Platform

基于 Amazon Bedrock AgentCore 的企业级 AI Agents 平台，让企业团队能够创建、部署和管理 AI Agent。

## 项目结构

```
ai-agents-platform/
├── backend/    # 后端服务 (Python + FastAPI)
├── frontend/   # 前端应用 (React + TypeScript + Vite)
├── infra/      # 基础设施 (AWS CDK + TypeScript)
├── docs/       # 项目文档
└── scripts/    # 工具脚本
```

## 技术栈

| 子项目 | 架构模式 | 技术栈 |
|--------|---------|--------|
| 后端 | DDD + Modular Monolith + Clean Architecture | Python 3.12 / FastAPI / SQLAlchemy 2.0 / MySQL 8.0 |
| 前端 | Feature-Sliced Design (FSD) | React 19 / TypeScript / Vite / TailwindCSS 4 |
| 基础设施 | Construct 分层 (L1→L2→L3) | AWS CDK / TypeScript |

## 快速开始

### 后端开发

```bash
cd backend
uv sync
uv run uvicorn src.presentation.api.main:app --reload --port 8000
```

### 前端开发

```bash
cd frontend
pnpm install
pnpm dev
```

### 基础设施

```bash
cd infra
pnpm install
pnpm cdk synth    # 合成 CloudFormation 模板
pnpm cdk diff     # 查看变更
```

### 本地数据库

```bash
docker run -d --name mysql-dev \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=changeme \
  -e MYSQL_DATABASE=ai_agents_platform \
  mysql:8.0
```

## 文档

| 文档 | 说明 |
|------|------|
| [开发贡献指南](docs/CONTRIB.md) | 环境准备、可用脚本、CI/CD、Git 工作流 |
| [运维手册](docs/RUNBOOK.md) | 部署流程、监控告警、故障排查、回滚 |
| [后端规范](backend/.claude/CLAUDE.md) | 后端架构、代码风格、测试规范 |
| [前端规范](frontend/.claude/CLAUDE.md) | 前端架构、组件设计、状态管理 |
| [CDK 规范](infra/.claude/CLAUDE.md) | 基础设施架构、Stack 设计 |
| [通用规范](.claude/CLAUDE.md) | 项目概述、会话协议、跨项目规则 |

## 贡献指南

请参考 [docs/CONTRIB.md](docs/CONTRIB.md) 获取完整的开发环境搭建和工作流指南。

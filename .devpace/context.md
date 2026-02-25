# 技术约定

> AI Agents Platform 的技术约定

## 技术栈

- **后端**: Python 3.12+ / FastAPI / SQLAlchemy 2.0 (async) / Alembic / Pydantic V2
- **前端**: React 19 / TypeScript / FSD 架构
- **基础设施**: AWS CDK (TypeScript) / ECS Fargate / Aurora MySQL / S3 / Bedrock
- **AI SDK**: claude-agent-sdk 0.1.35 / bedrock-agentcore 1.3.0
- **质量工具**: ruff / mypy / pytest / pytest-asyncio

## 编码规范

- 异步优先：AsyncSession + asyncio.to_thread() 包装同步 SDK
- DDD 四层：domain → application → infrastructure → api
- 跨模块通信：shared/domain/interfaces/
- 中文注释和文档
- Git 提交：<类型>(<范围>): <中文描述>

## 项目约定

- asyncio.gather 不可用于同一 AsyncSession 的并发操作
- uv run 执行所有 Python 命令
- Alembic 迁移 ID 使用随机 hex

## 架构约束

- 模块隔离 R1: 模块间不直接 import
- SDK-First: 外部服务封装 < 100 行
- providers.py 是唯一 Composition Root

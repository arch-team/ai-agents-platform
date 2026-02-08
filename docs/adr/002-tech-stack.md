# ADR-002: 技术栈选型

- **日期**: 2026-02-08
- **状态**: 已采纳

## 背景

需要选择后端技术栈，需与 Amazon Bedrock AgentCore Python SDK 生态兼容，同时支持异步高并发场景。

## 决策

Python 3.11+ / FastAPI / SQLAlchemy 2.0+ (async) / MySQL 8.0+ (Aurora) / uv / Ruff / pytest 8.0+

## 理由

- **Python**: Bedrock AgentCore SDK 和 Claude Agent SDK 均为 Python 优先
- **FastAPI**: 原生 async 支持，Pydantic v2 集成，OpenAPI 自动生成
- **SQLAlchemy 2.0+**: 统一的 async/sync API，成熟的 ORM + asyncmy 驱动
- **Aurora MySQL**: 与企业现有 AWS 基础设施一致，Aurora 提供高可用
- **uv**: 比 pip/poetry 快 10-100x，锁文件确保可重复构建

备选方案：
- Go + Gin — 性能更优，但与 Bedrock Python SDK 不兼容
- Django — 功能完整但异步支持不如 FastAPI 原生

## 影响

- 版本矩阵详见 `backend/.claude/rules/tech-stack.md`
- 包管理仅使用 uv，禁止 pip/poetry
- 代码检查仅使用 Ruff，禁止 flake8/black

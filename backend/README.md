# AI Agents Platform — 后端服务

基于 Amazon Bedrock AgentCore 的企业级 AI Agents 平台后端服务。

## 技术栈

- **语言**: Python 3.11+
- **Web 框架**: FastAPI
- **ORM**: SQLAlchemy 2.0+ (async)
- **数据库**: MySQL 8.0+ / Aurora MySQL 3.x
- **包管理**: uv

## 快速开始

```bash
# 安装依赖
uv sync --dev

# 运行开发服务器
uv run uvicorn src.presentation.api.main:app --reload --port 8000

# 运行测试
uv run pytest

# 代码检查
uv run ruff check src/
uv run mypy src/
```

## 项目结构

```
backend/
├── src/                    # 源代码
│   ├── modules/            # 业务模块
│   ├── shared/             # 共享内核
│   └── presentation/api/   # FastAPI 入口
├── tests/                  # 测试代码
├── migrations/             # 数据库迁移 (Alembic)
└── pyproject.toml          # 项目配置
```

详细规范请参考 `.claude/` 目录下的文档。

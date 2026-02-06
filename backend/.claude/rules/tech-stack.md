# 技术栈规范 (Tech Stack Standards)

> **职责**: 技术栈版本要求的**单一真实源**，包括 Python、FastAPI、SQLAlchemy 等核心依赖版本。

---

## §0 速查卡片

### 版本要求矩阵

| 类别 | 技术 | 最低版本 | 推荐版本 |
|------|------|---------|---------|
| **语言** | Python | >=3.11 | 3.12+ |
| **Web 框架** | FastAPI | >=0.110.0 | 0.115+ |
| **ASGI 服务器** | Uvicorn | >=0.27.0 | 0.30+ |
| **数据验证** | Pydantic | >=2.6.0 | 2.x |
| **ORM** | SQLAlchemy (async) | >=2.0.25 | 2.0+ |
| **数据库迁移** | Alembic | >=1.13.0 | 1.13+ |
| **数据库** | MySQL | 8.0+ | Aurora MySQL 3.x |
| **AWS SDK** | boto3 | >=1.34.0 | 1.34+ |
| **认证** | python-jose, passlib | - | - |
| **日志** | structlog | >=24.1.0 | 24.x |
| **包管理** | uv | - | 最新 |
| **代码检查** | Ruff | - | 最新 |
| **类型检查** | MyPy | - | 最新 |
| **测试** | pytest | >=8.0.0 | 8.x |

### 关键约束

- **包管理器**: 仅使用 uv，禁止 pip/poetry
- **代码检查**: 仅使用 Ruff，禁止 flake8/black/isort
- **类型检查**: MyPy `strict` 模式

### 快速验证命令

```bash
# 检查核心版本
python --version && uv --version

# 检查依赖版本
uv run python -c "import fastapi; print(fastapi.__version__)"
uv run python -c "import sqlalchemy; print(sqlalchemy.__version__)"
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [CLAUDE.md](../CLAUDE.md) | 技术栈概述和开发命令 |
| [testing.md](testing.md) | 测试规范 |
| [code-style.md](code-style.md) | 代码风格规范 |

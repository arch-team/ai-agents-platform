# 项目目录结构规范 (Project Structure)

> Claude 初始化或检查项目结构时优先查阅此文档

---

## 0. 速查卡片

### 项目根目录结构

```
{project}/                      # 后端backend
├── .claude/                    # Claude Code 上下文 (规范文档)
├── .github/workflows/          # CI/CD 工作流
├── doc/                        # 项目文档 (API/架构/指南)
├── migrations/                 # 数据库迁移 (Alembic)
├── scripts/                    # 工具脚本
├── src/                        # 源代码 → architecture.md
│   ├── modules/                # 业务模块
│   ├── shared/                 # 共享内核
│   └── presentation/api/       # FastAPI 入口
├── tests/                      # 测试代码 → testing.md
│   ├── conftest.py             # 全局 Fixture
│   ├── modules/                # 镜像 src/modules/ 结构 层测试
│   ├── shared/                 # shared/ 层测试
│   └── e2e/                    # 端到端测试
├── .env.example                # 环境变量模板
├── .gitignore                  # Git 忽略规则
├── .pre-commit-config.yaml     # pre-commit 钩子
├── pyproject.toml              # 项目配置 (uv/ruff/mypy/pytest)
└── README.md                   # 项目说明
```

### 配置文件速查

| 文件 | 用途 | 必须 |
|------|------|:----:|
| `pyproject.toml` | 项目和工具配置 | ✅ |
| `.gitignore` | Git 忽略规则 | ✅ |
| `.env.example` | 环境变量模板 | ✅ |
| `README.md` | 项目说明 | ✅ |
| `.pre-commit-config.yaml` | pre-commit 钩子 | 推荐 |
| `docker-compose.yml` | 本地开发环境 | 可选 |

### 禁止事项

| 规则 | 说明 |
|------|------|
| ❌ 根目录放业务代码 | 所有业务代码必须在 `src/` 下 |
| ❌ 测试散落源码目录 | 测试必须在 `tests/`，镜像 `src/` 结构 |
| ❌ 配置文件散落各处 | 配置统一在根目录或 `.claude/` |
| ❌ 临时文件入版本控制 | `.gitignore` 必须排除 |

---

## 1. 跨文档引用

| 内容 | 参考文档 |
|------|---------|
| `src/modules/{module}/` 内部结构 | [architecture.md](architecture.md) §6 |
| `tests/modules/{module}/` 结构 | [testing.md](testing.md) §1 |
| `.claude/rules/` 内容 | [README.md](../README.md) |

---

## 2. 新项目初始化检查清单

### 目录
- [ ] `src/` + `src/modules/` + `src/shared/` 已创建
- [ ] `src/presentation/api/main.py` 存在
- [ ] `tests/` + `tests/conftest.py` 已创建
- [ ] `.claude/CLAUDE.md` 已配置

### 配置文件
- [ ] `pyproject.toml` 包含 uv/ruff/mypy/pytest 配置
- [ ] `.gitignore` 排除 `__pycache__/`, `.venv/`, `.env`
- [ ] `.env.example` 列出必要环境变量
- [ ] `README.md` 包含项目说明

---

## PR Review 检查清单

- [ ] 新文件放置在正确目录
- [ ] 测试在 `tests/` 下，镜像 `src/` 结构
- [ ] 新 Python 包有 `__init__.py`
- [ ] 无临时文件被提交

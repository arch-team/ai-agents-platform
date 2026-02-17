# 开发贡献指南

> **自动生成**: 基于 `pyproject.toml`, `package.json`, `.env.example` 等配置文件
> **最后更新**: 2026-02-17

---

## 1. 环境准备

### 1.1 系统要求

| 工具 | 最低版本 | 推荐版本 | 说明 |
|------|---------|---------|------|
| Python | 3.11 | 3.12+ | 后端运行时 |
| Node.js | 18.0 | 22 LTS | 前端 + CDK + Claude Agent SDK 依赖 |
| uv | - | 最新 | 后端 Python 包管理 (禁止 pip/poetry) |
| pnpm | 8.0 | 10.x | 前端 + CDK 包管理 (禁止 npm/yarn) |
| Docker | - | 最新 | 本地数据库 |
| AWS CLI | 2.x | 最新 | CDK 部署 |

### 1.2 初始化

```bash
# 克隆仓库
git clone <repo-url> && cd ai-agents-platform

# 后端
cd backend && uv sync && cd ..

# 前端
cd frontend && pnpm install && cd ..

# 基础设施
cd infra && pnpm install && cd ..

# 启动本地 MySQL
docker compose up -d mysql
```

### 1.3 验证安装

```bash
# 后端
cd backend && uv run python -c "import fastapi; print(fastapi.__version__)"

# 前端
cd frontend && pnpm typecheck

# CDK
cd infra && pnpm exec cdk --version
```

---

## 2. 环境变量

### 2.1 后端 (`backend/.env.example`)

| 变量 | 默认值 | 说明 | 必填 |
|------|-------|------|:----:|
| `APP_NAME` | `ai-agents-platform` | 应用名称 | ✅ |
| `APP_ENV` | `development` | 运行环境 (`development` / `production`) | ✅ |
| `APP_DEBUG` | `true` | 调试模式 | ✅ |
| `DATABASE_HOST` | `localhost` | 数据库主机 | ✅ |
| `DATABASE_PORT` | `3306` | 数据库端口 | ✅ |
| `DATABASE_NAME` | `ai_agents_platform` | 数据库名 | ✅ |
| `DATABASE_USER` | `root` | 数据库用户 | ✅ |
| `DATABASE_PASSWORD` | `changeme` | 数据库密码 (部署环境由 Secrets Manager 注入) | ✅ |
| `JWT_SECRET_KEY` | `changeme-use-a-strong-secret-key` | JWT 签名密钥 (部署环境由 Secrets Manager 注入) | ✅ |
| `JWT_ALGORITHM` | `HS256` | JWT 算法 | ✅ |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token 有效期 (分钟) | ✅ |
| `AWS_REGION` | `us-east-1` | AWS 区域 | ✅ |
| `LOG_LEVEL` | `DEBUG` | 日志级别 (`DEBUG`/`INFO`/`WARNING`/`ERROR`) | ✅ |

> 部署环境通过 ECS Secrets (`ecs.Secret.fromSecretsManager`) 或 Secrets Manager ARN 注入敏感凭证。

### 2.2 前端 (`frontend/.env.example`)

| 变量 | 默认值 | 说明 | 必填 |
|------|-------|------|:----:|
| `VITE_API_BASE_URL` | `http://localhost:8000` | 后端 API 地址 | ✅ |

---

## 3. 可用脚本

### 3.1 后端 (uv + pyproject.toml)

| 命令 | 说明 |
|------|------|
| `uv run ruff check src/` | 代码检查 (lint) |
| `uv run ruff check src/ --fix` | 代码检查 + 自动修复 |
| `uv run ruff format src/` | 代码格式化 |
| `uv run mypy src/` | 类型检查 (strict 模式) |
| `uv run pytest` | 运行所有测试 |
| `uv run pytest --cov=src --cov-report=term-missing` | 测试 + 覆盖率 |
| `uv run pytest -m "unit"` | 仅运行单元测试 |
| `uv run pytest -m "integration"` | 仅运行集成测试 |
| `uv run pytest --mysql` | 使用 MySQL 运行测试 (需启动 mysql-test 容器) |
| `uv run uvicorn src.presentation.api.main:app --reload --port 8000` | 开发模式启动 |
| `uv run bandit -r src/` | 安全静态分析 |
| `uv run pip-audit` | 依赖漏洞扫描 |
| **一键验证** | |
| `uv run ruff check src/ && uv run ruff format --check src/ && uv run mypy src/ && uv run pytest --cov=src --cov-fail-under=85` | PR 前必跑 |

### 3.2 前端 (pnpm + package.json)

| 命令 | 说明 |
|------|------|
| `pnpm dev` | 开发模式启动 (Vite) |
| `pnpm build` | 构建生产版本 (`tsc -b && vite build`) |
| `pnpm preview` | 预览生产构建 |
| `pnpm lint` | ESLint 检查 |
| `pnpm lint:fix` | ESLint 检查 + 自动修复 |
| `pnpm format` | Prettier 格式化 |
| `pnpm format:check` | 格式化检查 |
| `pnpm typecheck` | TypeScript 类型检查 |
| `pnpm test` | 运行测试 (Vitest) |
| `pnpm test:watch` | 监听模式测试 |
| `pnpm test:coverage` | 测试 + 覆盖率 |
| `pnpm test:ui` | Vitest UI 模式 |
| **一键验证** | |
| `pnpm lint && pnpm format:check && pnpm typecheck && pnpm test:coverage` | PR 前必跑 |

### 3.3 基础设施 (pnpm + AWS CDK)

| 命令 | 说明 |
|------|------|
| `pnpm build` | TypeScript 编译 |
| `pnpm watch` | TypeScript 监听编译 |
| `pnpm test` | 运行 Jest 测试 |
| `pnpm test:watch` | 监听模式测试 |
| `pnpm test:coverage` | 测试 + 覆盖率 |
| `pnpm lint` | ESLint 检查 |
| `pnpm lint:fix` | ESLint 检查 + 自动修复 |
| `pnpm format` | Prettier 格式化 |
| `pnpm format:check` | 格式化检查 |
| `pnpm typecheck` | TypeScript 类型检查 |
| `pnpm cdk synth` | 合成 CloudFormation 模板 |
| `pnpm cdk diff` | 查看变更 |
| `pnpm cdk deploy` | 部署到 AWS |
| `pnpm cdk deploy --all` | 部署所有 Stack |
| `pnpm cdk list` | 列出所有 Stack |
| **一键验证** | |
| `pnpm lint && pnpm format:check && pnpm typecheck && pnpm cdk synth && pnpm test:coverage` | PR 前必跑 |

---

## 4. Docker 开发环境

### 4.1 docker-compose 服务

| 服务 | 端口 | 说明 |
|------|------|------|
| `mysql` | 3306 | 开发数据库 (MySQL 8.0) |
| `backend` | 8000 | 后端 API 服务 |
| `mysql-test` | 3307 | 测试数据库 (需 `--profile test` 启动) |

### 4.2 常用命令

```bash
# 启动开发数据库
docker compose up -d mysql

# 启动完整开发环境
docker compose up -d

# 启动测试数据库 (集成测试用)
docker compose --profile test up -d mysql-test

# 查看日志
docker compose logs -f backend

# 停止并清理
docker compose down -v
```

---

## 5. 测试流程

### 5.1 测试策略

| 子项目 | 单元测试 | 集成测试 | E2E | 覆盖率要求 |
|--------|:--------:|:--------:|:---:|:---------:|
| 后端 | `pytest -m unit` | `pytest -m integration` | - | ≥85% |
| 前端 | `pnpm test` | MSW Mock | Playwright | ≥80% |
| CDK | `pnpm test` (Fine-grained + Snapshot + CDK Nag) | - | - | ≥85% |

### 5.2 后端测试层级

| 层级 | 覆盖 | Mock 策略 |
|------|------|----------|
| Unit | Entity, Service, 领域逻辑 | Mock 外部依赖 (Repo, SDK) |
| Integration | API 端点, 仓库实现 | SQLite (默认) / MySQL (`--mysql`) |

### 5.3 TDD 工作流

```
1. 🔴 Red: 先写失败的测试
2. 🟢 Green: 编写最少代码使测试通过
3. 🔄 Refactor: 重构代码，保持测试通过
```

---

## 6. CI/CD 管道

### 6.1 后端 CI (`backend-ci.yml`)

| 阶段 | 触发条件 | 内容 |
|------|---------|------|
| lint-and-unit-test | `backend/**` 变更 | Ruff + MyPy + pytest (非集成) + 覆盖率 ≥85% |
| integration-test | lint 通过后 | MySQL 8.0 Service Container + 集成测试 |
| security-scan | lint 通过后 | Bandit + pip-audit (不阻断) |

### 6.2 CDK 部署 (`cdk-deploy.yml`)

```
push to main → [test] → [deploy-dev] → [deploy-prod (需审批)]
PR → [test] → [cdk-diff → PR 评论]
```

---

## 7. Git 工作流

### 7.1 分支策略

```
feat/{module-name} → main
```

### 7.2 提交规范

```
<类型>(<范围>): <简短描述>

类型: feat | fix | docs | style | refactor | test | chore
范围: backend | frontend | infra | docs | *
```

### 7.3 PR 检查清单

- [ ] 代码检查通过 (lint + typecheck)
- [ ] 测试通过且覆盖率达标
- [ ] 文档/注释使用中文
- [ ] 提交信息格式正确
- [ ] 无安全漏洞

---

## 8. 项目架构概览

| 子项目 | 架构模式 | 技术栈 |
|--------|---------|--------|
| 后端 | DDD + Modular Monolith + Clean Architecture | Python 3.11+ / FastAPI / SQLAlchemy 2.0+ / MySQL 8.0+ |
| 前端 | Feature-Sliced Design (FSD) | React 19 / TypeScript / Vite / TailwindCSS 4 |
| CDK | Construct 分层 (L1→L2→L3) | AWS CDK / TypeScript |

---

## 相关文档

| 文档 | 说明 |
|------|------|
| `backend/.claude/CLAUDE.md` | 后端规范入口 |
| `frontend/.claude/CLAUDE.md` | 前端规范入口 |
| `infra/.claude/CLAUDE.md` | CDK 规范入口 |
| `docs/RUNBOOK.md` | 运维手册 |
| `.github/DEPLOYMENT.md` | CI/CD 部署配置 |

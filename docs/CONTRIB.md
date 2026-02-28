# 开发贡献指南

> **自动生成**: 基于 `pyproject.toml`, `package.json`, `.env.example` 等配置文件
> **最后更新**: 2026-02-27

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
docker run -d --name mysql-dev -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=changeme \
  -e MYSQL_DATABASE=ai_agents_platform mysql:8.0
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
| `DEFAULT_ADMIN_EMAIL` | `admin@company.com` | 默认管理员邮箱 (启动时自动创建，幂等) | ✅ |
| `DEFAULT_ADMIN_PASSWORD` | `Admin@2026!` | 默认管理员密码 | ✅ |
| `DEFAULT_ADMIN_NAME` | `系统管理员` | 默认管理员名称 | ✅ |
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

### 4.1 本地数据库

```bash
# 启动开发数据库
docker run -d --name mysql-dev \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=changeme \
  -e MYSQL_DATABASE=ai_agents_platform \
  mysql:8.0

# 启动测试数据库 (集成测试用)
docker run -d --name mysql-test \
  -p 3307:3306 \
  -e MYSQL_ROOT_PASSWORD=test_root_password \
  -e MYSQL_DATABASE=ai_agents_test \
  mysql:8.0

# 查看容器状态
docker ps --filter "name=mysql"

# 停止并清理
docker rm -f mysql-dev mysql-test
```

### 4.2 后端镜像构建

```bash
# 构建后端 API 镜像
cd backend && docker build -t ai-agents-platform:latest .

# 构建 Agent 运行时镜像
cd backend && docker build -f Dockerfile.agent -t ai-agents-agent:latest .
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

### 6.1 工作流架构

采用**可复用工作流**模式，质量检查逻辑提取为独立工作流，被 CI 和 Deploy 共同调用：

```
backend-quality.yml  ← backend-ci.yml (PR/push)
                     ← backend-deploy.yml (部署前质量门控)

frontend-quality.yml ← frontend-ci.yml (PR/push)
                     ← frontend-deploy.yml (部署前质量门控)
```

### 6.2 后端 CI/CD

| 工作流 | 触发条件 | 内容 |
|--------|---------|------|
| `backend-ci.yml` | PR/push `backend/**` | 调用 `backend-quality.yml` (Ruff + MyPy + pytest + 覆盖率 ≥83%) |
| `backend-quality.yml` | 可复用工作流 | MySQL 8.0 Service Container + lint + 类型检查 + 测试 (排除 E2E) |
| `backend-deploy.yml` | push to main `backend/src/**` | 质量门控 → Dev 自动部署 → Prod 手动审批 (支持回滚) |

### 6.3 前端 CI/CD

| 工作流 | 触发条件 | 内容 |
|--------|---------|------|
| `frontend-ci.yml` | PR/push `frontend/**` | 调用 `frontend-quality.yml` (lint + typecheck + test + build) |
| `frontend-deploy.yml` | push to main `frontend/src/**` | 质量门控 → Dev 部署 → Prod 手动审批 (支持回滚) |

### 6.4 基础设施 & Agent 镜像

| 工作流 | 触发条件 | 内容 |
|--------|---------|------|
| `cdk-deploy.yml` | push to main `infra/**` | test → deploy-dev → deploy-prod (需审批) |
| `agent-image.yml` | push to main `backend/Dockerfile.agent` | Agent 运行时镜像构建推送 ECR |
| `deploy-notify.yml` | 部署工作流完成 | 部署失败时自动创建 GitHub Issue 通知 |

### 6.5 通用优化

- **最小权限原则**: 所有工作流默认 `permissions: {}`，各 job 按需声明
- **并发控制**: 同一分支/PR 上的新推送自动取消旧的运行
- **版本统一**: UV、Python、Node.js、pnpm 版本通过环境变量集中管理

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

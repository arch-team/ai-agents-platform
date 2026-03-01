# 贡献指南

感谢你对 AI Agents Platform 的关注！本文档说明如何参与项目贡献。

---

## 分支策略（GitHub Flow）

本项目采用 **GitHub Flow** — 单主分支 `main`，所有变更通过 Feature 分支 + Pull Request 合并。

```
main (受保护，禁止直接推送)
  ├── feat/agent-streaming   ← 新功能
  ├── fix/auth-token-expire  ← Bug 修复
  ├── docs/update-readme     ← 文档更新
  └── chore/bump-fastapi     ← 依赖/构建
```

### 分支命名规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feat/` | 新功能 | `feat/agent-memory` |
| `fix/` | Bug 修复 | `fix/sse-timeout` |
| `docs/` | 文档更新 | `docs/api-reference` |
| `refactor/` | 重构 | `refactor/auth-module` |
| `chore/` | 构建/依赖/CI | `chore/upgrade-cdk` |
| `test/` | 测试补充 | `test/agent-execution` |

---

## 贡献流程

### 1. 创建 Feature 分支

```bash
git checkout main
git pull origin main
git checkout -b feat/your-feature
```

### 2. 开发并提交

遵循项目的提交规范（详见 `.claude/rules/common.md`）：

```bash
# 提交格式
git commit -m "feat(backend): 添加 Agent 流式输出支持"
git commit -m "fix(frontend): 修复登录页面表单验证"
```

提交类型：`feat` / `fix` / `docs` / `style` / `refactor` / `test` / `chore`
范围：`backend` / `frontend` / `infra` / `docs` / `*`（多个子项目）

### 3. 推送并创建 PR

```bash
git push origin feat/your-feature
```

在 GitHub 上创建 Pull Request，目标分支为 `main`。

### 4. 代码审查

- PR 需要至少 1 人审批
- CI 检查必须全部通过（lint、类型检查、测试）
- 使用 Squash and Merge 合并，保持 `main` 提交历史整洁
- 合并后 Feature 分支自动删除

---

## CI/CD 流水线

### PR 阶段（自动触发）

| 变更路径 | 触发工作流 | 检查内容 |
|---------|-----------|---------|
| `backend/**` | Backend CI | ruff + mypy + pytest + 集成测试 + 安全扫描 |
| `frontend/**` | Frontend CI | ESLint + TypeScript + Vitest + E2E |
| `infra/**` | CDK Deploy | lint + typecheck + test + CDK Synth + CDK Diff |
| `.github/workflows/**` | Workflow Lint | actionlint 语法校验 |

### 合并到 main 后（自动部署）

1. **Dev 环境** — 自动部署
2. **Prod 环境** — 需要手动审批后部署

---

## 本地开发环境

详细的开发环境设置请参考 [docs/CONTRIB.md](docs/CONTRIB.md)。

快速开始：

```bash
# 后端
cd backend && uv sync
uv run uvicorn src.presentation.api.main:app --reload --port 8000

# 前端
cd frontend && pnpm install && pnpm dev

# 基础设施
cd infra && pnpm install && pnpm cdk synth
```

---

## 代码规范

### 通用

- 文档和代码注释使用**中文**
- 代码变量名、函数名、类名使用**英文**
- 禁止造轮子 — 优先使用成熟第三方库（详见 `.claude/rules/common.md`）

### 后端（Python）

- 代码风格：`ruff` 格式化 + 检查
- 类型检查：`mypy --strict`
- 测试覆盖率：≥ 85%
- 架构模式：DDD + Clean Architecture

### 前端（TypeScript）

- 代码风格：ESLint + Prettier
- 类型检查：`tsc --noEmit`
- 架构模式：Feature-Sliced Design (FSD)

### 基础设施（CDK）

- 代码风格：ESLint
- 类型检查：`tsc --noEmit`
- 必须通过 `cdk synth` 验证

---

## 质量检查

提交 PR 前，请在本地运行：

```bash
# 后端
cd backend
uv run ruff check src/
uv run mypy src/
uv run pytest

# 前端
cd frontend
pnpm lint
pnpm typecheck
pnpm test

# 基础设施
cd infra
pnpm lint
pnpm typecheck
pnpm test
```

---

## 问题反馈

- 使用 GitHub Issues 报告 Bug 或提出功能建议
- Issue 标题使用中文，标签使用英文

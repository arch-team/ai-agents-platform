---
name: quality-gate
description: 一键运行所有子项目的质量检查（lint + type check + test）
---

对 Monorepo 的三个子项目依次运行完整质量检查，汇总结果。

## 执行步骤

### 1. 后端 (Python / FastAPI)

```bash
cd backend && uv run ruff check src/ && uv run ruff format --check src/ && uv run mypy src/ && uv run pytest --cov=src --cov-fail-under=85
```

### 2. 前端 (React / TypeScript)

```bash
cd frontend && pnpm lint && pnpm format:check && pnpm typecheck && pnpm test
```

### 3. 基础设施 (AWS CDK)

```bash
cd infra && pnpm lint && pnpm format:check && pnpm typecheck && pnpm test
```

## 输出格式

每个子项目报告：通过/失败 + 失败详情摘要。最后给出总体状态。

```
## 质量检查报告

| 子项目 | Lint | Format | Type Check | Test | 状态 |
|--------|------|--------|------------|------|------|
| backend | ✅ | ✅ | ✅ | ✅ 85%+ | PASS |
| frontend | ✅ | ✅ | ✅ | ✅ | PASS |
| infra | ✅ | ✅ | ✅ | ✅ | PASS |

**总体: PASS / FAIL**
```

如有失败项，列出具体错误摘要和修复建议。

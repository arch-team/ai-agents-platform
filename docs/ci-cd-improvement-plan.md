# CI/CD 自动化成熟度差距分析与改进方案

## Context

AI Agents Platform 已有 10 个 GitHub Actions 工作流、17 个 pre-commit 钩子、2071+ 测试（88.29% 覆盖率）、完善的 Dependabot 配置。但从"需求到生产全自动化、功能质量变更全保障"的标准看，仍有可量化的差距。

本方案按 **八个维度** 分析差距，按 **四波次 ROI 排序** 给出可执行的改进计划。

---

## 差距总览（按严重程度）

| 严重程度 | 数量 | 含义 |
|---------|------|------|
| **P1** 阻断/影响发布 | 8 项 | 生产质量保障缺口 |
| **P2** 影响效率 | 12 项 | 运维效率和安全合规 |
| **P3** 锦上添花 | 4 项 | 开发者体验提升 |

---

## 维度 1: 需求到代码的追踪

**现状**: 需求管理依赖 `docs/progress.md` 手工维护，commitizen 验证格式但不关联 Issue。

| # | 差距 | P | 复杂度 |
|---|------|---|--------|
| 1.1 | 缺少 PR 模板（`.github/pull_request_template.md` 不存在） | P2 | 低 |
| 1.2 | 缺少 Issue 模板（`.github/ISSUE_TEMPLATE/` 不存在） | P2 | 低 |
| 1.3 | 缺少自动化 PR 标签（基于变更路径打 `backend`/`frontend`/`infra` 标签） | P3 | 低 |

### 方案

- **1.1** 创建 `.github/pull_request_template.md`：变更类型 checkbox + 关联 Issue + 测试说明 + 自查清单
- **1.2** 创建 `.github/ISSUE_TEMPLATE/bug_report.yml` + `feature_request.yml`（YAML 表单格式）
- **1.3** 新增 `.github/labeler.yml` + `actions/labeler@v5` 工作流，按路径自动打标签

---

## 维度 2: 代码质量自动化

**现状**: 后端质量门禁完善（Ruff + MyPy strict + 85% 覆盖率 + 架构合规测试）。前端有差距。

| # | 差距 | P | 复杂度 |
|---|------|---|--------|
| 2.1 | 前端无覆盖率门禁 — `frontend-quality.yml:37` 只运行 `pnpm test`，不检查覆盖率 | P1 | 低 |
| 2.2 | 前端安全扫描不阻断 — `frontend-quality.yml:46` pnpm audit 仅 echo warning | P2 | 低 |

### 方案

- **2.1** 修改 `frontend-quality.yml`：`pnpm test` → `pnpm test:coverage`；在 `vitest.config.ts` 添加 `coverage.thresholds.lines = 80`
- **2.2** 将 `pnpm audit --audit-level=high` 的输出上传 artifact，critical 级别阻断

---

## 维度 3: 测试自动化完整性

**现状**: 单元/集成测试完善，E2E 和性能测试配置存在但未集成 CI。

| # | 差距 | P | 复杂度 |
|---|------|---|--------|
| 3.1 | E2E 测试未集成 CI — Playwright 已配置但 `frontend-ci.yml` 不跑 `pnpm test:e2e` | P1 | 中 |
| 3.2 | 部署后冒烟测试过于简单 — `backend-deploy.yml` 仅检查 `/health` HTTP 200 | P1 | 中 |
| 3.3 | 性能测试完全手动 — Locust 脚本存在 (`scripts/loadtest/`) 但无自动触发 | P2 | 中 |
| 3.4 | 缺少 API 契约测试 — 前后端无 OpenAPI schema 自动验证 | P2 | 中 |

### 方案

- **3.1** `frontend-ci.yml` 新增 `e2e-test` job：安装 Playwright chromium → `pnpm test:e2e` → 上传 `playwright-report/` artifact
- **3.2** `backend-deploy.yml` 健康检查后增加业务端点冒烟测试：验证 `/health/ready` + 关键 API 端点可达性
- **3.3** 新增 `.github/workflows/performance-test.yml`：每周一 schedule 触发 Locust 对 Dev 环境压测，上传 CSV 报告
- **3.4** 后端 FastAPI 自动生成 OpenAPI schema，前端 CI 对比 schema 验证 API 兼容性

---

## 维度 4: 部署自动化成熟度

**现状**: 部署流程完整（Dev 自动 → Prod 审批），有回滚支持。数据库迁移嵌入容器启动。

| # | 差距 | P | 复杂度 |
|---|------|---|--------|
| 4.1 | 数据库迁移无 CI 前置验证 — 迁移嵌入 `Dockerfile CMD`，失败只能靠 ECS 健康检查重启 | P1 | 中 |
| 4.2 | 迁移回滚未自动化 — 回滚时仅重部署旧代码，不降级数据库 schema | P1 | 中 |
| 4.3 | 前端部署验证不足 — 仅检查 S3 文件存在，不验证 CloudFront 可访问 | P2 | 低 |
| 4.4 | 缺少部署超时保护 — ECS 部署无明确超时，长时间卡死无自动终止 | P2 | 低 |

### 方案

- **4.1** `backend-deploy.yml` 部署前新增 `validate-migration` step：对 SQLite 内存库执行 `alembic check` 验证迁移脚本语法
- **4.2** 在 `backend-deploy.yml` 的 rollback 模式中增加数据库降级选项（`alembic downgrade` 到目标 revision）
- **4.3** `frontend-deploy.yml` 增加 CloudFront URL 可达性验证（等待缓存失效后 curl 检查）
- **4.4** CDK ComputeStack 中为 ECS 部署添加 `deploymentConfiguration.deploymentCircuitBreaker` 的超时配置

---

## 维度 5: 发布管理

**现状**: 版本号硬编码 `0.1.0`，无 tag/changelog/release 自动化。

| # | 差距 | P | 复杂度 |
|---|------|---|--------|
| 5.1 | 无自动化版本管理 — 版本号硬编码，无 semantic versioning | P2 | 中 |
| 5.2 | 无 Changelog 自动化 — 无基于 commit 历史的 changelog 生成 | P2 | 中 |
| 5.3 | 无 Git tag 发布流程 — 部署不绑定版本标签，回滚需手动查找 commit SHA | P2 | 低 |

### 方案

- **5.1 + 5.2** 新增 `.github/workflows/release.yml`：使用 `git-cliff` 生成 changelog + `softprops/action-gh-release` 创建 GitHub Release
- **5.3** `backend-deploy.yml` Prod 部署成功后自动打 `deploy-prod-YYYYMMDD-HHMMSS` tag

---

## 维度 6: 可观测性与反馈循环

**现状**: 7 个 CloudWatch 告警（资源级），部署失败自动创建 Issue。

| # | 差距 | P | 复杂度 |
|---|------|---|--------|
| 6.1 | 缺少应用级错误追踪 — 无 ERROR 日志聚合告警，生产异常依赖手动查 CloudWatch Logs | P1 | 中 |
| 6.2 | 缺少 API 延迟告警 — 7 个告警均为资源指标，无 P95/P99 延迟监控 | P1 | 低 |
| 6.3 | 缺少部署后指标自动对比 — 部署后无自动对比错误率/延迟与部署前基线 | P2 | 中 |
| 6.4 | 缺少 DORA 指标统计 — 无部署频率、变更前置时间、MTTR 等度量 | P3 | 低 |

### 方案

- **6.1** `infra/lib/stacks/monitoring-stack.ts` 新增 CloudWatch Logs Metric Filter：过滤 `"level":"error"` 日志 → 创建 ErrorCount 告警（阈值 5/5min）
- **6.2** MonitoringStack 新增 ALB Target Response Time P95 告警（阈值 500ms）
- **6.3** 部署工作流添加 `aws cloudwatch get-metric-statistics` 比对部署前后 5XX 率和延迟
- **6.4** 使用 `github/issue-metrics` action 或自定义脚本统计部署频率

---

## 维度 7: 安全自动化

**现状**: Bandit + pip-audit + Trivy + CDK Nag + Dependabot（5 ecosystem），已比较完善。

| # | 差距 | P | 复杂度 |
|---|------|---|--------|
| 7.1 | pip-audit 不阻断 CI — `backend-ci.yml:131` 设置 `continue-on-error: true` | P1 | 低 |
| 7.2 | 缺少定期安全扫描 — 仅代码变更时触发，无周期性全量扫描 | P2 | 中 |
| 7.3 | 缺少 DAST 动态安全测试 — 无运行时安全扫描 | P2 | 高 |
| 7.4 | 缺少依赖许可证审计 — pip-audit 检查漏洞但不检查 License 合规 | P3 | 低 |

### 方案

- **7.1** `backend-ci.yml:131` 将 `continue-on-error: true` → `false`（或至少对 critical/high 漏洞阻断）
- **7.2** 新增 `.github/workflows/security-scan.yml`：每周一 schedule 触发全量 Bandit + pip-audit + Trivy 扫描，报告上传 artifact（保留 90 天）
- **7.3** 中长期引入 OWASP ZAP 对 Dev 环境进行 DAST 扫描
- **7.4** 在安全扫描工作流中添加 `pip-licenses` 检查

---

## 维度 8: 灾备与恢复自动化

**现状**: Aurora PITR + 快照恢复脚本存在，ECS Circuit Breaker 自动回滚。

| # | 差距 | P | 复杂度 |
|---|------|---|--------|
| 8.1 | 备份验证未自动化 — Aurora 快照恢复未定期自动验证 | P2 | 中 |
| 8.2 | 缺少基础设施漂移检测 — 无定期 `cdk diff` 检测代码与实际资源偏差 | P2 | 中 |
| 8.3 | 缺少自动灾备演练 — 灾备脚本存在但完全手动执行 | P2 | 高 |

### 方案

- **8.1** 新增 `.github/workflows/backup-verify.yml`：每月 1 号 schedule 检查最新 Aurora 快照状态
- **8.2** 新增 `.github/workflows/drift-detection.yml`：每周 schedule 执行 `cdk diff`，有漂移自动创建 Issue
- **8.3** 中长期将 `scripts/dr-aurora-restore.sh` 集成到月度 schedule 工作流

---

## 实施计划（四波次 ROI 排序）

### Wave 1: 快速见效（1-2 周，~3 人天）

> 低复杂度高回报，立即提升质量保障。

| 序号 | 改进项 | 修改目标 | 工时 |
|------|--------|---------|------|
| W1-1 | pip-audit 阻断策略 (7.1) | `backend-ci.yml:131` | 0.5h |
| W1-2 | 前端覆盖率门禁 (2.1) | `frontend-quality.yml` + `vitest.config.ts` | 2h |
| W1-3 | PR 模板 (1.1) | 新建 `.github/pull_request_template.md` | 1h |
| W1-4 | Issue 模板 (1.2) | 新建 `.github/ISSUE_TEMPLATE/*.yml` | 1h |
| W1-5 | PR 自动标签 (1.3) | 新建 `.github/labeler.yml` + 工作流 | 1h |
| W1-6 | 部署版本 tag (5.3) | `backend-deploy.yml` Prod job 末尾 | 1h |

### Wave 2: 核心能力（2-4 周，~8 人天）

> 补齐 P1 级生产质量保障缺口。

| 序号 | 改进项 | 修改目标 | 工时 |
|------|--------|---------|------|
| W2-1 | API 延迟告警 (6.2) | `infra/lib/stacks/monitoring-stack.ts` | 3h |
| W2-2 | 应用错误追踪 (6.1) | `infra/lib/stacks/monitoring-stack.ts` | 4h |
| W2-3 | 部署后冒烟测试 (3.2) | `backend-deploy.yml` deploy-dev/prod job | 4h |
| W2-4 | 数据库迁移前置验证 (4.1) | `backend-deploy.yml` 新增 step | 3h |
| W2-5 | E2E 测试集成 CI (3.1) | `frontend-ci.yml` 新增 e2e-test job | 4h |
| W2-6 | 迁移回滚自动化 (4.2) | `backend-deploy.yml` rollback 模式增强 | 4h |

### Wave 3: 运维成熟（1-2 月，~6 人天）

> 周期性自动化 + 发布管理 + 安全增强。

| 序号 | 改进项 | 修改目标 | 工时 |
|------|--------|---------|------|
| W3-1 | 定期安全扫描 (7.2) | 新建 `.github/workflows/security-scan.yml` | 3h |
| W3-2 | 版本管理 + Changelog (5.1+5.2) | 新建 `.github/workflows/release.yml` + `cliff.toml` | 6h |
| W3-3 | 性能测试自动化 (3.3) | 新建 `.github/workflows/performance-test.yml` | 4h |
| W3-4 | 备份验证 (8.1) | 新建 `.github/workflows/backup-verify.yml` | 3h |
| W3-5 | 基础设施漂移检测 (8.2) | 新建 `.github/workflows/drift-detection.yml` | 3h |
| W3-6 | 前端部署验证增强 (4.3) | `frontend-deploy.yml` | 2h |

### Wave 4: 高级能力（按需，~12 人天）

> 高复杂度项，用户量增长后再投入。

| 序号 | 改进项 | 工时 | 触发条件 |
|------|--------|------|---------|
| W4-1 | API 契约测试 (3.4) | 3d | 前后端频繁 API 不兼容时 |
| W4-2 | DAST 动态安全测试 (7.3) | 3d | 面向外网开放或合规要求 |
| W4-3 | 部署后指标自动对比 (6.3) | 2d | 部署频率 > 每日 1 次 |
| W4-4 | 自动灾备演练 (8.3) | 3d | 用户量 > 100 |
| W4-5 | DORA 指标统计 (6.4) | 1d | 团队扩大需度量效率 |

---

## 实施后工作流全景

```
开发者提交代码
  │
  ├─ pre-commit (17 hooks) ──── 本地质量门禁
  │
  ├─ PR 创建 ──── 自动打标签 + PR 模板
  │    │
  │    ├─ backend-ci: lint → unit test (85%) → MySQL 集成 → 安全扫描 (阻断)
  │    ├─ frontend-ci: lint → typecheck → test (80%) → E2E (Playwright) → build
  │    ├─ cdk-deploy: lint → typecheck → test → synth → cdk diff (PR 评论)
  │    └─ workflow-lint: actionlint + 安全模式检查
  │
  ├─ merge to main ──── 部署流水线
  │    │
  │    ├─ quality-gate ──── 全量质量检查
  │    ├─ validate-migration ──── 数据库迁移前置验证 [NEW]
  │    ├─ deploy-dev ──── CDK deploy → 健康检查 → 冒烟测试 [ENHANCED]
  │    ├─ deploy-prod ──── (人工审批) → CDK diff → CDK deploy → 冒烟测试 → 打 tag [ENHANCED]
  │    └─ deploy-notify ──── 成功摘要 / 失败创建 Issue
  │
  ├─ 定期 schedule [NEW]
  │    ├─ 每周一: 安全全量扫描 + 基础设施漂移检测 + 性能测试
  │    ├─ 每月 1 号: 备份验证
  │    └─ 按需: Release (版本号 + Changelog + GitHub Release)
  │
  └─ 运行时监控
       ├─ CloudWatch 告警 (7 现有 + 2 新增: 错误率 + P95 延迟) [ENHANCED]
       ├─ 部署失败 → GitHub Issue
       └─ Dependabot → 每周依赖更新 PR (5 ecosystem)
```

---

## 文件变更清单

### 新建文件（9 个）

| 文件 | 用途 |
|------|------|
| `.github/pull_request_template.md` | PR 模板 |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | Bug 报告模板 |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | 功能请求模板 |
| `.github/labeler.yml` | 路径→标签映射 |
| `.github/workflows/labeler.yml` | PR 自动标签工作流 |
| `.github/workflows/security-scan.yml` | 定期安全扫描 |
| `.github/workflows/performance-test.yml` | 定期性能测试 |
| `.github/workflows/backup-verify.yml` | 月度备份验证 |
| `.github/workflows/drift-detection.yml` | 基础设施漂移检测 |

### 修改文件（6 个）

| 文件 | 修改内容 |
|------|---------|
| `.github/workflows/backend-ci.yml` | pip-audit `continue-on-error` → `false` |
| `.github/workflows/backend-deploy.yml` | 迁移前置验证 + 冒烟测试增强 + Prod 打 tag + rollback 数据库降级 |
| `.github/workflows/frontend-ci.yml` | 新增 E2E 测试 job |
| `.github/workflows/frontend-quality.yml` | `pnpm test` → `pnpm test:coverage` |
| `.github/workflows/frontend-deploy.yml` | CloudFront 可达性验证 |
| `infra/lib/stacks/monitoring-stack.ts` | 新增 ErrorCount + P95 Latency 告警 |

### 可选新建（Wave 3-4）

| 文件 | 用途 |
|------|------|
| `.github/workflows/release.yml` | 版本发布 + Changelog |
| `cliff.toml` | git-cliff changelog 配置 |
| `frontend/vitest.config.ts` 修改 | 覆盖率阈值配置 |

---

## 验证方式

1. **Wave 1 验证**: 提交含已知漏洞依赖的 PR → pip-audit 阻断 CI；提交前端代码低覆盖率 → 门禁失败
2. **Wave 2 验证**: 部署后检查冒烟测试日志；在 MonitoringStack 部署后确认 CloudWatch 新增 2 个告警
3. **Wave 3 验证**: 等待 schedule 触发后检查工作流运行记录和 artifact 输出
4. **全局验证**: 对比实施前后的工作流数量（10 → 15+）和质量门禁覆盖点

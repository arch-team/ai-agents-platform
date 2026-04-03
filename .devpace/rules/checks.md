# 项目质量检查

> **职责**：定义本项目特有的质量检查。Monorepo 子项目分别检查。

## developing → verifying

<!-- Backend 检查 -->
- [ ] **Backend Lint**：后端代码规范检查
      检查方式：`cd backend && uv run ruff check src/`

- [ ] **Backend 类型检查**：后端类型安全检查
      检查方式：`cd backend && uv run mypy src/`

- [ ] **Backend 测试**：后端单元测试和集成测试
      检查方式：`cd backend && uv run pytest --cov=src --cov-fail-under=85`

<!-- Frontend 检查 -->
- [ ] **Frontend Lint**：前端代码规范检查
      检查方式：`cd frontend && pnpm lint`

- [ ] **Frontend 类型检查**：前端类型安全检查
      检查方式：`cd frontend && pnpm typecheck`

- [ ] **Frontend 测试**：前端单元测试
      检查方式：`cd frontend && pnpm test:coverage`

<!-- devpace 内置检查（不可删除） -->
- [ ] **需求完整性**：CR 意图 section 与变更复杂度匹配
      检查方式：Claude 检查意图字段填充度（简单=用户原话；标准=+范围+验收条件；复杂=全部字段）

## verifying → in_review

<!-- 意图检查 -->
- [ ] **架构一致性**：变更符合各子项目架构规范
      检查方式：Claude 检查 backend 遵循 DDD 分层，frontend 遵循 FSD 依赖规则，无跨模块直接依赖

- [ ] **安全规范**：无安全隐患（硬编码密钥、SQL 注入、XSS 风险）
      检查方式：Claude 检查敏感数据是否通过环境变量管理，输入是否经过验证，敏感信息是否记录到日志

- [ ] **测试质量**：测试覆盖关键路径和边界条件
      检查方式：Claude 检查是否有针对主要业务逻辑的测试，异常路径是否覆盖

<!-- devpace 内置检查（不可删除） -->
- [ ] **意图一致性**：实际变更与 CR 意图 section 的范围和验收条件一致
      检查方式：Claude 对比 git diff 与意图 section，标注偏差

# 项目质量检查

> **职责**：定义 AI Agents Platform 的质量检查项。

## developing → verifying

<!-- 命令检查 -->
- [ ] **Ruff 代码规范**：Python 代码通过 ruff 静态检查
      检查方式：cd backend && uv run ruff check .

- [ ] **MyPy 类型检查**：Python 代码通过 mypy 类型检查
      检查方式：cd backend && uv run mypy .
      依赖：Ruff 代码规范

- [ ] **单元测试**：所有测试通过，覆盖率 >= 85%
      检查方式：cd backend && uv run pytest tests/ -v
      依赖：MyPy 类型检查
      阈值：85%

<!-- 意图检查 -->
- [ ] **架构合规**：变更遵循 DDD + Modular Monolith 架构规范
      检查方式：Claude 检查 模块边界不被打破（无跨模块直接 import，仅通过 shared/interfaces 通信）

<!-- devpace 内置检查（不可删除） -->
- [ ] **需求完整性**：CR 意图 section 与变更复杂度匹配
      检查方式：Claude 检查意图字段填充度（简单=用户原话；标准=+范围+验收条件；复杂=全部字段）

## verifying → in_review

<!-- 命令检查 -->
- [ ] **全量测试**：后端全部测试通过
      检查方式：cd backend && uv run pytest tests/ -v --tb=short

<!-- 意图检查 -->
- [ ] **SDK-First 合规**：新增外部服务调用遵循 SDK-First 原则（封装 < 100 行）
      检查方式：Claude 检查 新增的外部服务适配器是否超过 100 行，是否直接使用成熟 SDK

<!-- 对抗审查 -->
- [ ] **对抗审查**：假设代码存在问题，必须找出至少 1 个问题或改进建议
      检查方式：Claude 对抗审查 检查边界条件处理、错误路径覆盖和安全隐患

<!-- devpace 内置检查（不可删除） -->
- [ ] **意图一致性**：实际变更与 CR 意图 section 的范围和验收条件一致
      检查方式：Claude 对比 git diff 与意图 section，标注偏差

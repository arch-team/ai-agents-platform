# AI Agents Platform - Claude Code 上下文管理优化方案

## 质量评估报告

### 文件统计

| 层级 | 文件数 | 总行数 |
|------|--------|--------|
| 根级 (.claude/) | 3 | ~150 |
| 后端 (backend/.claude/) | 11 | ~2,500 |
| 前端 (frontend/.claude/) | 14 | ~2,000 |
| 基础设施 (infra/.claude/) | 12 | ~2,100 |
| **合计** | **40** | **~6,750** |

### 各子项目 CLAUDE.md 评分

| 维度 (满分) | 根级 | 后端 | 前端 | Infra |
|-------------|------|------|------|-------|
| Commands/Workflows (20) | 5 | 17 | 16 | 18 |
| Architecture Clarity (20) | 15 | 16 | 17 | 15 |
| Non-Obvious Patterns (15) | 10 | 10 | 10 | 11 |
| Conciseness (15) | 14 | 9 | 13 | 10 |
| Currency (15) | 12 | 12 | 12 | 10 |
| Actionability (15) | 14 | 8 | 10 | 10 |
| **总分** | **70** | **72** | **78** | **74** |

前端 CLAUDE.md (154行) 是当前最精简的范本，其他子项目应参考此风格。

---

## 发现的关键问题

### 红旗 1（严重）：PROJECT_CONFIG 不会被 Claude Code 自动加载

Claude Code 自动加载的文件：
- `~/.claude/CLAUDE.md` (全局)
- `.claude/CLAUDE.md` (项目级)
- `.claude/rules/*.md` (规则文件)

**不会自动加载的文件**：
- `.claude/README.md`
- `.claude/PROJECT_CONFIG.*.md`

这意味着项目最有价值的业务配置（模块列表、域事件、Stack 列表、违规检测规则）放在了 Claude Code 不会自动加载的位置。Claude 在生成代码时**不知道项目有哪些模块和域事件**。

### 红旗 2（严重）：README.md 完全浪费 (529行)

三个 `.claude/README.md`（后端165行、前端179行、infra185行）是给人类维护者的目录导航，Claude Code 既不自动加载也不需要。

### 红旗 3（严重）：PROJECT_CONFIG.template.md 不应在 .claude/ 中 (405行)

模板文件只在"创建新项目"时使用，在日常开发中完全无用。分散在三个子项目中增加维护负担。

### 红旗 4（中等）：通用知识占用大量 token

`accessibility.md`(268行)、`performance.md`(301行)、`security.md`(253行) 中大量内容是 Claude 已掌握的通用知识（WCAG标准、React.memo使用场景、XSS防护）。写入 rules/ 只增加 token 消耗，不改善输出质量。

### 红旗 5（中等）：代码模板过于完整

`architecture.md` 中的 Entity/Repository/DI 模板、`state-management.md` 中的 Zustand Store 模板等完整代码模板，适合放在 `doc/templates/` 按需查阅，而非强制加载到每次对话。

### 红旗 6（低等）：三个子项目大量重复内容

包管理命令(pnpm install/add/remove)在前端和infra完全重复，TDD工作流在三个子项目中重复，安全基础原则在三个子项目中重复。

---

## 整体架构优劣势

### 优势（应保留）

1. **SSoT 原则执行良好** - 每个关键概念都有"单一真实源"标注
2. **速查卡片设计 (Section 0) 是亮点** - 信息密度最高的部分，Claude 能快速定位规则
3. **职责边界声明清晰** - `> **职责**: ...` 和 `> **职责边界**: ...` 减少文档模糊地带
4. **符号化表达统一** - `✅/❌/🔴/🟡/🟢` 让 Claude 快速识别约束
5. **占位符模板系统** - `{Entity}`, `{module}` 为代码生成提供结构化指引

### 劣势（需改进）

1. **加载策略与文件组织不匹配** - PROJECT_CONFIG 不被自动加载
2. **总量过大** - 每个子项目 2000-2500 行，推荐 500-1000 行
3. **通用知识过度文档化** - 很多内容 Claude 已掌握
4. **跨文件引用过多** - 大量"详见 xxx"增加理解间接性
5. **与 SuperClaude 全局配置重叠** - 测试诚信、Git规范等重复定义

---

## 优化建议（按优先级排序）

### P0 - 立即执行（结构性修复）

#### 1. 将 PROJECT_CONFIG 核心内容合并到 CLAUDE.md 或移入 rules/

**方案 A（推荐）**：重命名为 `rules/project-config.md` 使其被自动加载
**方案 B**：将核心内容（模块列表、域事件、违规检测规则）合并到 CLAUDE.md

涉及文件：
- `backend/.claude/PROJECT_CONFIG.ai-agents-platform.md` → `backend/.claude/rules/project-config.md`
- `frontend/.claude/PROJECT_CONFIG.ai-agents-platform.md` → `frontend/.claude/rules/project-config.md`
- `infra/.claude/PROJECT_CONFIG.ai-agents-platform.md` → `infra/.claude/rules/project-config.md`

#### 2. 删除所有 .claude/README.md（节省529行）

这些文件对 Claude Code 完全无用。如需人类维护文档，放在 `doc/claude-context-guide.md`。

涉及文件（删除）：
- `backend/.claude/README.md`
- `frontend/.claude/README.md`
- `infra/.claude/README.md`

#### 3. 移出所有 PROJECT_CONFIG.template.md（节省405行）

移到 `doc/templates/` 目录，不污染 `.claude/` 上下文。

涉及文件（移动）：
- `backend/.claude/PROJECT_CONFIG.template.md` → `doc/templates/backend-project-config.template.md`
- `frontend/.claude/PROJECT_CONFIG.template.md` → `doc/templates/frontend-project-config.template.md`
- `infra/.claude/PROJECT_CONFIG.template.md` → `doc/templates/infra-project-config.template.md`

### P1 - 短期优化（精简内容）

#### 4. 精简通用知识内容（预计节省 1,500+ 行）

核心原则：**只保留项目特有的决策和约束，删除 Claude 已掌握的通用知识**

| 文件 | 当前行数 | 目标行数 | 精简策略 |
|------|---------|---------|---------|
| `backend/rules/architecture.md` | 657 | ~300 | 保留 §0 速查卡片+核心分层规则，精简代码模板 |
| `frontend/rules/accessibility.md` | 268 | ~60 | 只保留"必须 WCAG AA"和项目特有 ARIA 规则表 |
| `frontend/rules/performance.md` | 301 | ~80 | 只保留决策流程图和 Memoization 决策表 |
| `frontend/rules/state-management.md` | 319 | ~100 | 只保留决策流程图和文件位置速查 |
| `frontend/rules/component-design.md` | 282 | ~100 | 只保留组件类型速查和 Props 设计速查 |
| `frontend/rules/security.md` | 253 | ~60 | 只保留速查表和禁止事项 |
| `backend/rules/code-style.md` | 324 | ~80 | 只保留命名速查和 Docstring 原则 |
| `backend/rules/security.md` | 252 | ~60 | 只保留速查表和检测命令 |
| `infra/rules/project-structure.md` | 243 | ~60 | 只保留目录树和配置速查 |
| `infra/rules/cost-optimization.md` | 179 | ~60 | 只保留环境资源矩阵和必须标签 |

#### 5. 精简 CLAUDE.md 命令部分

删除各子项目中的通用包管理命令（install/add/remove），只保留：
- 一键检查命令
- 核心测试命令
- 启动/部署命令
- 子项目特有命令（如 CDK synth/deploy）

涉及文件：
- `backend/.claude/CLAUDE.md` - 精简 "环境管理(uv)" 和 "测试" 章节
- `frontend/.claude/CLAUDE.md` - 精简 "环境管理(pnpm)" 章节
- `infra/.claude/CLAUDE.md` - 精简 "环境管理(pnpm)" 章节，删除 frontmatter

#### 6. 删除 CLAUDE.md 中的"相关规范文档"导航表

rules/ 文件会被自动加载，导航表浪费空间。改为在 CLAUDE.md 开头一行说明即可。

### P2 - 中期优化（消除重复）

#### 7. 将共享规则提升到根级 common.md

TDD 工作流描述、安全基础原则等在三个子项目中重复的内容，统一放入根级 `.claude/rules/common.md`。

#### 8. 低频规范移出 rules/ 避免自动加载

将以下文件移到 `doc/standards/` 或类似位置，在 CLAUDE.md 中添加一行提示：
- `infra/rules/deployment.md` - 只在部署时需要
- `infra/rules/cost-optimization.md` - 只在成本评审时需要

### P3 - 远期建议

#### 9. 实际编码后再完善规范

当前项目处于"规范定义阶段"，建议在实际编码中遇到 Claude 生成不符预期的代码时，再逐步添加对应规则（问题驱动 > 规范驱动）。

---

## 优化后目标

| 指标 | 当前 | 优化后 | 变化 |
|------|------|--------|------|
| 总文件数 | 40 | ~24 | -40% |
| 总行数 | ~6,750 | ~2,800 | -58% |
| 每子项目 rules 行数 | 1,500-2,500 | 600-900 | -60% |
| PROJECT_CONFIG 自动加载 | 否 | 是 | 修复 |
| README.md 浪费 | 529行 | 0 | 消除 |
| Template 浪费 | 405行 | 0 | 移出 |

---

## 验证方法

1. **加载验证**：在各子项目目录下启动 Claude Code 新会话，确认 PROJECT_CONFIG（重命名后）的内容出现在上下文中
2. **功能验证**：让 Claude 生成一个新模块的代码，确认它知道项目的模块列表和架构约束
3. **token 验证**：对比优化前后的首次对话 token 消耗（可通过 Claude Code 的 /cost 命令查看）

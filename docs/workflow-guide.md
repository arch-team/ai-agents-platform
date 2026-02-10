# Claude Code 开发迭代工作流指南

> **文档类型**: 操作指南 | **适用范围**: 所有子项目 | **前置要求**: 已安装 Claude Code CLI

---

## 1. 工作流概述

本项目采用**文档驱动开发**模式：以现有文档体系驱动 Claude Code 进行持续迭代开发。核心枢纽是 `docs/progress.md`，它既是"状态记录器"，也是"任务驱动器"。

### 1.1 文档角色分工

```
docs/strategy/roadmap.md        ──→  决定"做什么"（Phase / Milestone / 模块 / 验收标准）
        │
        ▼
docs/progress.md                ──→  驱动"下一步"（任务列表 + 状态追踪 + 会话记录）
        │
        ▼
backend/.claude/rules/*         ──→  指导"怎么做"（架构 / 代码风格 / 测试 / 安全规范）
        │
        ▼
backend/.claude/rules/checklist.md ──→  验证"做得对不对"（PR 检查清单）
        │
        ▼
docs/progress.md                ──→  记录"做完了什么"（更新状态，闭合循环）
```

### 1.2 关键文件索引

| 文件 | 作用 | 何时读取 |
|------|------|---------|
| `docs/progress.md` | 任务驱动器，当前进度与待做任务 | **每次会话开始** |
| `docs/strategy/roadmap.md` | 四阶段路线图，里程碑定义 | 开始新 Milestone 时 |
| `docs/strategy/improvement-plan.md` | 变更来源，深度审查行动项 | 注入变更时 + 执行变更时读取详细方案 |
| `backend/.claude/rules/*` | 编码规范 (11 份) | 实现具体任务时 (Claude Code 自动加载) |
| `docs/adr/*.md` | 架构决策记录 | 遇到架构选择时 |

---

## 2. progress.md 结构说明

`docs/progress.md` 包含以下区域，从上到下：

| 区域 | 内容 | 更新时机 |
|------|------|---------|
| **当前状态** | 阶段、里程碑、变更积压摘要、下一步行动 | 每次会话结束 |
| **模块状态** | 各模块开发进度总览 | 模块状态变更时 |
| **基础设施** | CDK Stack 部署状态 | 基础设施变更时 |
| **当前 Milestone 任务拆解** | 可执行任务列表 (含依赖、参考规范) | 开始新 Milestone / 任务完成时 |
| **变更积压** | 按 S0~S4 分级的变更列表 (来自深度审查) | 变更注入 / 变更完成时 |
| **遗留事项** | 跨会话传递的未完成项和注意点 | 发现遗留问题时 |
| **近期会话** | 最近 5 条会话记录 (表格格式) | 每次会话结束 (插入新行) |

### 任务状态定义

| 状态 | 含义 |
|------|------|
| 待开始 | 尚未启动 |
| 进行中 | 当前会话正在实现 |
| 已完成 | 实现并通过验证 |
| 阻塞 | 因外部依赖或问题无法继续，详情记录在"遗留事项" |

---

## 3. 五种典型会话场景

### 场景 1：开始新 Milestone（任务拆解）

当一个 Milestone 即将开始、progress.md 中尚无该 Milestone 的任务拆解时使用。

**提示词：**
```
读取 docs/progress.md 和 docs/strategy/roadmap.md。
为 M2 里程碑创建任务拆解列表，更新到 progress.md 的"当前 Milestone 任务拆解"区。
```

**Claude Code 执行逻辑：**
1. 读取 progress.md 了解当前状态
2. 读取 roadmap.md 获取目标 Milestone 的交付物和验收标准
3. 将粗粒度模块拆解为可执行的原子任务
4. 标注任务间依赖关系和参考规范
5. 更新 progress.md

---

### 场景 2：日常开发（实现具体任务）

最常见的会话类型。每次会话完成 1-3 个任务。

**提示词：**
```
读取 docs/progress.md，完成任务 #2 和 #3（shared/domain 层）。
遵循 TDD 工作流：先写测试，再实现。
会话结束时更新 progress.md。
```

**Claude Code 执行逻辑：**
1. 读取 progress.md，定位任务 #2 和 #3 的内容、依赖和参考规范
2. 确认前置任务 (#1) 已完成
3. 加载对应的 rules 文件 (如 `rules/architecture.md` §5)
4. 按 TDD 流程实现：先写测试 → 再写实现 → 运行测试验证
5. 更新 progress.md：任务状态改为"已完成"，记录会话日期

**简化提示词（适合顺序推进时）：**
```
读取 docs/progress.md，继续下一个待开始的任务。
```

---

### 场景 3：质量验收

在 Milestone 的所有实现任务完成后，执行最终验收。

**提示词：**
```
读取 docs/progress.md，执行 M1 验收：
- ruff check + mypy + pytest --cov-fail-under=85
- 对照 backend/.claude/rules/checklist.md 逐项检查
- 对照 docs/strategy/roadmap.md M1 验收标准检查
更新 progress.md。
```

**Claude Code 执行逻辑：**
1. 运行自动化质量检查 (ruff, mypy, pytest)
2. 逐项对照 checklist.md 检查
3. 对照 roadmap.md 中的验收标准表
4. 如有未通过项，记录到"遗留事项"
5. 全部通过后，更新 Milestone 状态和模块状态

---

### 场景 4：架构决策

开发过程中遇到需要权衡取舍的技术方案选择时使用。

**提示词：**
```
我在 [具体场景] 遇到了 [选择 A 和选择 B]。
参考 docs/adr/README.md 的模板格式，创建新的 ADR。
```

**Claude Code 执行逻辑：**
1. 分析两种方案的优劣
2. 按 ADR 模板创建 `docs/adr/00X-*.md`
3. 在 progress.md 的"上次会话"中记录决策

---

### 场景 5：变更注入与执行

当深度审查（如 `docs/strategy/improvement-plan.md`）产出了变更行动项，需要将其注入工作流执行。

#### 场景 5a：变更注入（一次性操作）

从 improvement-plan.md 提取行动项，转化为 progress.md 的变更积压表。

**提示词：**
```
读取 docs/strategy/improvement-plan.md，将 S0~S4 行动项注入 docs/progress.md 的变更积压表。
S5 不入积压表，保留在 improvement-plan.md 按季度评审。
```

**Claude Code 执行逻辑：**
1. 读取 improvement-plan.md 提取各级别行动项
2. 在 progress.md 新增/更新变更积压区域，按 S0~S4 分表
3. 使用 `C-SX-Y` 编号（如 C-S0-1），与 Milestone 任务的 `#N` 视觉区分
4. 更新当前状态区的变更积压摘要行

---

#### 场景 5b：执行变更（日常操作）

从变更积压表选择任务执行，流程类似场景 2。

**提示词：**
```
读取 docs/progress.md，执行变更 C-S0-5（is_active 检查）。
遵循 TDD 工作流。会话结束时更新 progress.md。
```

**Claude Code 执行逻辑：**
1. 读取 progress.md 定位变更 C-S0-5
2. 读取 improvement-plan.md 对应章节获取详细修复方案和验证标准
3. 按 TDD 流程实现：先写测试 → 再写实现 → 运行测试验证
4. 更新 progress.md：变更状态改为"已完成"，更新统计表

**简化提示词（顺序执行变更时）：**
```
读取 docs/progress.md，继续下一个待开始的 S0 变更。
```

---

#### 场景 5c：变更评审（定期操作）

定期审查变更积压进度和相关性，确保变更列表保持最新。

**提示词：**
```
读取 docs/progress.md 的变更积压表，评审当前进度。
检查是否有变更已过时或优先级需要调整。
```

**Claude Code 执行逻辑：**
1. 汇总各级别完成进度
2. 对比 improvement-plan.md 检查是否有新增发现需要补充
3. 检查是否有变更因环境变化而过时（如 S3-1 数据库选型已决策，可移除）
4. 建议优先级调整（如有）

---

## 4. 会话三步协议

每次与 Claude Code 交互遵循固定的三步流程：

```
┌─────────────────────────────────────────────────────┐
│  步骤 1: 开始                                        │
│  "读取 docs/progress.md"                             │
│  → Claude Code 获知：当前进度、待做任务、变更积压、遗留事项 │
├─────────────────────────────────────────────────────┤
│  步骤 2: 执行                                        │
│  告知本次要完成的任务编号或目标                         │
│  → Claude Code 自动加载对应 rules 作为编码标准         │
├─────────────────────────────────────────────────────┤
│  步骤 3: 结束                                        │
│  Claude Code 更新 progress.md                        │
│  → 任务状态、模块状态、变更积压、遗留事项、近期会话     │
└─────────────────────────────────────────────────────┘
```

### 结束时 progress.md 更新内容

| 更新区域 | 更新内容 |
|---------|---------|
| 当前状态 | "下一步"指向下一个待开始任务；更新变更积压摘要 |
| 模块状态 | 如模块整体完成则更新状态 |
| 任务拆解表 | 已完成任务状态改为"已完成"，填写会话日期 |
| 变更积压表 | 已完成变更状态改为"已完成"，填写会话日期；更新统计 |
| 遗留事项 | 新增/清除遗留项 |
| 近期会话 | 在表头插入新行（保留最近 5 条） |

---

## 5. 任务与规范的映射关系

Claude Code 在执行具体任务时，通过 progress.md 任务表中的"参考规范"列定位需要遵循的规范文件。以下是 M1 的映射示例：

| 任务领域 | 参考规范文件 | 关注章节 |
|---------|------------|---------|
| 目录结构初始化 | `rules/project-structure.md` | 初始化检查清单 |
| DDD 实体/仓储/值对象 | `rules/architecture.md` | §5 DDD 战术模式 |
| 事件驱动通信 | `rules/architecture.md` | §4.2 EventBus |
| 数据库/配置 | `rules/tech-stack.md` + `rules/sdk-first.md` | 技术选型约束 |
| API 设计 | `rules/api-design.md` | 错误格式、分页 |
| 健康检查 | `rules/observability.md` | §1 Health Check |
| 测试 | `rules/testing.md` | TDD + AAA 模式 |
| 认证授权 | `rules/security.md` | JWT, RBAC, 密码哈希 |
| 最终验收 | `rules/checklist.md` | PR 检查清单 |

---

## 6. Milestone 生命周期

```
┌──────────────┐     ┌──────────────────────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. 任务拆解  │ ──► │  2. 逐项实现 + 变更穿插       │ ──► │  3. 质量验收  │ ──► │  4. 推进下一个 │
│  (场景 1)     │     │  (场景 2 × N) + (场景 5b × M) │     │  (场景 3)     │     │  Milestone    │
└──────────────┘     └──────────────────────────────┘     └──────────────┘     └──────────────┘
    读取 roadmap         Milestone 任务与变更交替执行       运行检查工具          更新 progress
    拆解为任务           每 2-3 个任务穿插 S1/S2 变更      对照 checklist       归档已完成 Milestone
    写入 progress        S0 阻断时优先处理变更              对照 roadmap 验收     拆解新 Milestone

                         ┌─ 任务 #1 ─► 任务 #2 ─► C-S1-1 ─► 任务 #3 ─► 任务 #4 ─► C-S2-1 ─► ...
    穿插示例:            │  (Milestone)            (变更)    (Milestone)            (变更)
                         └─ S0 全部完成后，Milestone 任务与 S1/S2 变更交替推进
```

### Milestone 完成后的操作

1. progress.md 中已完成的 Milestone 任务表保留但折叠 (可用 `<details>` 标签)
2. 模块状态表更新为"已完成"
3. 从 roadmap.md 拆解下一个 Milestone 的任务
4. "当前状态"更新为新 Milestone

---

## 7. 反馈循环

开发过程中产生的各类产出，各归其位：

| 产出类型 | 归档位置 | 触发条件 |
|---------|---------|---------|
| 任务进度 | `docs/progress.md` 任务拆解表 | 每次会话结束 |
| 变更进度 | `docs/progress.md` 变更积压表 | 变更完成时 |
| 变更来源 | `docs/strategy/improvement-plan.md` | 执行变更时读取详细方案 |
| 开发发现 | `docs/progress.md` 变更积压表 (`C-D-N`) | 开发中发现问题且用户确认升级时 |
| 架构决策 | `docs/adr/00X-*.md` | 遇到需要权衡的技术方案选择 |
| 规范修正 | `backend/.claude/rules/*.md` | 发现规范与实际不符或需要补充 |
| 遗留事项 | `docs/progress.md` 遗留事项区 | 任务未完成或发现跨会话问题 |

---

## 8. 常见问答

### Q: 一次会话应该完成多少任务？

建议 1-3 个任务。任务粒度已按"单次会话可完成"设计。如果一个任务过大（实现中发现），应在 progress.md 中将其拆分为子任务。

### Q: 任务的依赖关系如何处理？

progress.md 任务表有"依赖"列。Claude Code 在执行任务前会检查前置任务是否已完成。如果前置未完成，会优先处理前置任务或告知用户。

### Q: 如果一个任务完成了一半怎么办？

1. 将任务状态标记为"进行中"
2. 在"遗留事项"区记录已完成和未完成的部分
3. 下次会话继续时，Claude Code 通过读取 progress.md 恢复上下文

### Q: 如何处理开发中发现的新需求？

1. 如果是当前 Milestone 范围内的补充任务，直接在任务拆解表中新增行
2. 如果超出当前 Milestone 范围，记录到"遗留事项"区并标注"待后续 Milestone 处理"

### Q: 规范文件和实际开发冲突怎么办？

按场景 4 创建 ADR 记录决策，并同步更新对应的 rules 文件。保持规范与代码的一致性。

### Q: 变更积压和 Milestone 任务的关系是什么？

变更积压与 Milestone 任务是两个并列通道。S0 变更优先级高于 Milestone 任务（阻断推进），S1/S2 与 Milestone 任务穿插执行，S3 需用户主动触发，S4 在 Phase 结束时集中处理。两者都通过 progress.md 统一管理。变更之间也有依赖关系（"依赖"列），Claude Code 会自动检查。

### Q: 如何从深度审查产出注入变更到工作流？

使用场景 5a（变更注入），读取 improvement-plan.md 提取 S0~S4 行动项，写入 progress.md 的变更积压区域。这是一次性操作，注入后变更自然进入会话循环。

### Q: 开发中发现了新 bug 怎么办？

如果 bug 阻断当前任务，立即记入变更积压表（编号 `C-D-N`）。如果不影响当前任务，先记入遗留事项，会话结束时 Claude Code 会提示是否升级为正式变更。详见 session-workflow.md §2.1。

### Q: 修改导致其他模块测试失败（回归）怎么处理？

Claude Code 会自动区分：当前模块失败 → 正常修复循环；其他模块失败 → 回归信号，暂停修复并报告影响范围，由用户决策继续修复/回滚/创建 ADR。详见 session-workflow.md §2.2。

### Q: 多人协作时如何使用这套工作流？

每人在开始会话前先 `git pull` 获取最新 progress.md，避免冲突。任务拆解表中可增加"负责人"列进行分工。

---

## 9. 快速参考卡

```
# 开始新会话
读取 docs/progress.md，完成任务 #N。

# 顺序推进
读取 docs/progress.md，继续下一个待开始的任务。

# 批量实现
读取 docs/progress.md，完成任务 #N 和 #M（XXX 层）。遵循 TDD。

# 质量验收
读取 docs/progress.md，执行 MX 验收。对照 checklist.md 和 roadmap.md 检查。

# 新 Milestone
读取 docs/progress.md 和 docs/strategy/roadmap.md。为 MX 创建任务拆解。

# 架构决策
我在 [场景] 遇到 [选择]。参考 docs/adr/README.md 创建 ADR。

# 查看状态
读取 docs/progress.md，汇报当前项目进度。

# 注入变更（一次性操作）
读取 docs/strategy/improvement-plan.md，将 S0~S4 行动项注入 docs/progress.md 的变更积压表。

# 执行指定变更
读取 docs/progress.md，执行变更 C-S0-5（is_active 检查）。遵循 TDD。

# 顺序执行变更
读取 docs/progress.md，继续下一个待开始的 S0 变更。

# 变更评审
读取 docs/progress.md 的变更积压表，评审当前进度，检查优先级是否需要调整。
```

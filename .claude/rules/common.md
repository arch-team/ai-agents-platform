# 跨项目通用规则 (Common Rules)

> 适用于所有子项目的通用规范

---

## Git 提交规范

### 提交信息格式

```
<类型>(<范围>): <简短描述>

<详细描述（可选）>

<关联 Issue（可选）>
```

### 类型

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 Bug |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构（非新功能/修复） |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖更新 |

### 范围

| 范围 | 说明 |
|------|------|
| `backend` | 后端服务 |
| `frontend` | 前端应用 |
| `infra` | 基础设施 |
| `docs` | 文档 |
| `*` | 多个子项目 |

### 示例

```bash
feat(backend): 添加用户认证模块
fix(frontend): 修复登录页面表单验证
docs(*): 更新 README 文档
chore(backend): 升级 FastAPI 到 0.111
```

---

## 禁止造轮子规则

> 🔴 **强制规则**: 所有子项目（backend/frontend/infra）必须遵守

**核心原则**: 凡是可以通过引入成熟第三方 SDK/库实现的功能，**禁止**自行从零实现。

### 决策流程

```
需要实现某功能?
    ↓
官方 SDK / 成熟第三方库支持? ──是──► 🟢 直接引入使用（必须）
    │
   否
    ↓
社区库可满足需求? ──是──► 🟡 评估后引入（Stars > 1K, 活跃维护, MIT/Apache）
    │
   否
    ↓
🔴 自行实现（需在 ADR 中记录理由，说明为何无可用库）
```

### 违规判定标准

以下情况视为**违规**:
- 手动实现 Rate Limiting 逻辑，而不使用 `slowapi`/`fastapi-limiter` 等库
- 手动实现 JWT 编解码，而不使用 `PyJWT`/`python-jose` 等库
- 手动实现 SSE 解析，而不使用 `httpx-sse`/`aiohttp-sse-client` 等库
- 手动实现表单验证逻辑，而不使用 `zod`/`yup` 等库
- 手动实现状态管理框架，而不使用 `zustand`/`jotai` 等库
- 手动实现 ORM/Query Builder，而不使用 `SQLAlchemy`/`Prisma` 等库
- 任何其他"成熟库已解决但选择自行编码"的场景

### 允许的例外

| 场景 | 允许自行实现 | 条件 |
|------|:-----------:|------|
| 薄封装层 | ✅ | SDK 之上 < 100 行的适配器（参考 `backend/.claude/rules/sdk-first.md`） |
| 项目特有的业务逻辑 | ✅ | 无通用库可满足的领域特定逻辑 |
| 简单工具函数 | ✅ | 引入整个库成本过高的简单工具（如 `formatDate`、`cn`） |
| 安全考量 | ✅ | 第三方库存在已知漏洞且无替代品 |

### 检测命令

```bash
# 审查时检查是否存在可用库替代的自行实现
# 后端: 参考 backend/.claude/rules/sdk-first.md 的 SDK 决策流程
# 前端: 参考 frontend/.claude/rules/tech-stack.md 的依赖列表
```

### PR Review 检查项

- [ ] 新增的功能实现是否有成熟第三方库可替代
- [ ] 如果自行实现，是否在 ADR 或代码注释中说明了理由
- [ ] 封装层是否超过 100 行（超过需评估是否应直接使用库）

---

## 代码审查标准

### 通用检查项

- [ ] 代码符合子项目规范
- [ ] 有充分的测试覆盖
- [ ] 无明显的安全漏洞
- [ ] 文档/注释使用中文
- [ ] 提交信息格式正确

---

## 文档规范

### 文件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 主规范 | `CLAUDE.md` | 各子项目入口（Claude Code 框架约定） |
| 专题规范 | `rules/{topic}.md` | `rules/testing.md`, `rules/checklist.md` |
| 项目配置 | `project-config.md` | 项目特定配置（非 Claude Code 加载） |
| 项目说明 | `README.md` | 项目根目录说明 |

**命名原则**: 除 `CLAUDE.md`（Claude Code 框架约定）和 `README.md` 外，所有文档统一使用 `kebab-case.md`

### 文档语言

- 所有文档内容使用中文
- 代码示例保持原始语言

---

## Monorepo 结构概览

> 本节是 Monorepo 结构的**单一真实源 (Single Source of Truth)**

```
ai-agents-platform/             # Monorepo 根目录
├── .claude/                    # 根级：通用规范
│   ├── CLAUDE.md               # 全局入口（语言、项目概述、会话协议）
│   └── rules/
│       ├── common.md           # 跨项目通用规则（本文件）
│       └── session-workflow.md # 会话工作流规则（三步循环、任务管理）
├── backend/                    # 后端项目 (Python + FastAPI)
├── frontend/                   # 前端项目 (React + TypeScript)
├── infra/                      # 基础设施项目 (AWS CDK)
├── docs/                       # 全局文档
│   ├── progress.md             # 项目进度追踪（每次会话必读）
│   ├── adr/                    # 架构决策记录 (ADR)
│   ├── strategy/               # 战略规划文档
│   └── template/               # 文档模板
├── .gitignore                  # 根级 gitignore
└── README.md                   # 项目总说明
```

各子项目的详细目录结构请参考对应的 `project-structure.md` 文档。

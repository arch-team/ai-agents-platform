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
| 上下文导航 | `context-guide.md` | 目录说明（非 Claude Code 加载） |
| 项目配置 | `project-config.md` | 项目特定配置（非 Claude Code 加载） |
| 模板 | `project-config.template.md` | 新项目配置模板 |
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
│   ├── CLAUDE.md               # 全局入口（语言、项目概述）
│   └── rules/
│       └── common.md           # 跨项目通用规则（本文件）
├── backend/                    # 后端项目 (Python + FastAPI)
├── frontend/                   # 前端项目 (React + TypeScript)
├── infra/                      # 基础设施项目 (AWS CDK)
├── doc/                        # 全局文档
├── .gitignore                  # 根级 gitignore
└── README.md                   # 项目总说明
```

各子项目的详细目录结构请参考对应的 `project-structure.md` 文档。

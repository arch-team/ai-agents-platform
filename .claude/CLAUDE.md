# AI Agents Platform - Monorepo

## 响应语言
**所有对话和文档必须（Must）使用中文。**
**除非有特殊说明，请用中文回答。** (Unless otherwise specified, please respond in Chinese.)

### 强制要求

- 所有对话必须使用中文
- 代码注释使用中文
- 文档内容使用中文
- Git 提交信息使用中文

### 例外情况

以下内容保持英文:
- 代码变量名、函数名、类名
- 技术术语 (如 API, SDK, TDD)
- 第三方库/框架名称
- 错误信息和日志 (可选)

---

## 项目概述

AI Agents Platform — 基于 Amazon Bedrock AgentCore 的企业内部 AI Agents 平台，让企业团队能够创建、部署和管理 AI Agent。

- **核心技术**: Amazon Bedrock AgentCore + Claude Agent SDK
- **架构模式**: DDD + Modular Monolith + Clean Architecture (后端) | FSD (前端) | CDK (基础设施)

---

## 会话协议

> 详细执行步骤见 `.claude/rules/session-workflow.md`（自动加载）

### 核心三步循环

1. **开始**: 读取 `docs/progress.md` → 识别当前 Milestone、待做任务、遗留事项、变更积压状态 → 向用户汇报
2. **执行**: 按任务表"参考规范"加载 rules → 检查前置依赖 → TDD 实现 → 质量检查
3. **结束**: 更新 `docs/progress.md` 六个区域（当前状态、模块状态、任务表、变更积压表、遗留事项、近期会话）

### 文档角色

| 文件 | 角色 | 何时读取 |
|------|------|---------|
| `docs/progress.md` | 任务驱动器 | **每次会话开始** |
| `docs/strategy/roadmap.md` | 决定"做什么" | 开始新 Milestone 时 |
| `docs/strategy/improvement-plan.md` | 变更来源 | 注入变更时 + 执行变更时读取详细方案 |
| `backend/.claude/rules/*` | 指导"怎么做" | 实现任务时 (自动加载) |
| `backend/.claude/rules/checklist.md` | 验证"做得对不对" | 验收和 PR 前 |

---

## Git 分支

```
feat/{module-name} → main
```

功能分支直接从 main 创建，完成后合并回 main。提交规范见 `.claude/rules/common.md`。

---

## Monorepo 结构

| 子项目 | 路径 | 说明 |
|--------|------|------|
| 后端服务 | `backend/` | Python + FastAPI |
| 前端应用 | `frontend/` | (计划中) |
| 基础设施 | `infra/` | (计划中) |

进入子目录后，Claude Code 自动加载该子项目的规范：

```bash
cd backend/   # 加载 backend/.claude/CLAUDE.md
cd frontend/  # 加载 frontend/.claude/CLAUDE.md
cd infra/     # 加载 infra/.claude/CLAUDE.md
```

---

## 相关文档

| 子项目 | 规范文档 |
|--------|---------|
| 后端 | [backend/.claude/CLAUDE.md](../backend/.claude/CLAUDE.md) |
| 通用规则 | [.claude/rules/common.md](.claude/rules/common.md) |

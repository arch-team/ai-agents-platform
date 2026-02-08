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
- **北极星指标**: 周活跃 Agent 数量 (WAA)

---

## 项目当前状态

> ⚠️ **每次会话开始时必须阅读 [docs/progress.md](../docs/progress.md) 了解最新进度**

**当前阶段**: Phase 1 MVP | **当前里程碑**: M1 项目脚手架 | **状态**: 未开始

### 四阶段路线

| 阶段 | 目标 | 后端模块 |
|------|------|---------|
| **Phase 1 MVP** (当前) | 端到端验证 | shared → auth → agents → execution |
| Phase 2 核心功能 | 10+ 模板 | tools → knowledge → monitoring → templates |
| Phase 3 生态扩展 | Multi-Agent | orchestration → evaluation → models |
| Phase 4 企业成熟 | 自助式使用 | audit → marketplace → analytics |

---

## 会话协议

### 会话开始

每次新 Claude Code 会话开始时:

1. **阅读进度**: 读取 `docs/progress.md` 了解当前状态和上次会话产出
2. **确认范围**: 明确本次会话要完成的具体模块或任务
3. **聚焦执行**: 一次会话聚焦一个模块的开发

### 会话结束

每次会话结束前:

1. **更新进度**: 更新 `docs/progress.md` 中的模块状态、会话日志
2. **记录决策**: 如有架构决策，追加 ADR 记录
3. **Git 提交**: 提交代码变更到对应的功能分支

### 会话启动模板

```
请阅读 docs/progress.md 了解项目当前进度。
今天要做的是: [具体任务描述]
```

---

## Git 分支策略

### 分支命名规范

```
main                           # 稳定主线，始终可部署
├── phase-1/m1-scaffold        # 里程碑分支: Phase 1 M1 脚手架
│   ├── feat/shared-module     # 功能分支: shared 模块
│   ├── feat/auth-module       # 功能分支: auth 模块
│   └── ...
├── phase-1/m2-agent-crud      # 里程碑分支: Phase 1 M2
└── phase-1/m3-e2e-demo        # 里程碑分支: Phase 1 M3
```

### 分支规则

| 规则 | 说明 |
|------|------|
| **功能分支** | `feat/{module}-{feature}` — 每个模块/功能一个分支 |
| **里程碑分支** | `phase-{n}/m{n}-{name}` — 聚合该里程碑所有功能分支 |
| **合并方向** | feat → milestone → main |
| **分支生命周期** | 功能完成 → PR Review → 合并 → 删除分支 |
| **禁止事项** | 不在 main 直接开发，不跨里程碑合并 |

### 开发节奏

```
会话 1: git checkout -b feat/shared-module → 开发 shared → 完成 → PR
会话 2: git checkout -b feat/auth-module   → 开发 auth   → 完成 → PR
会话 3: git checkout -b feat/agents-module → 开发 agents → 完成 → PR
...
每完成一个里程碑 → 合并到 main → 更新 docs/progress.md
```

---

## Monorepo 结构

| 子项目 | 路径 | 说明 |
|--------|------|------|
| 后端服务 | `backend/` | Python + FastAPI |
| 前端应用 | `frontend/` | (计划中) |
| 基础设施 | `infra/` | (计划中) |

## 开发指南

进入对应子目录后，Claude Code 会自动加载该子项目的规范：

```bash
cd backend/   # 加载后端规范
cd frontend/  # 加载前端规范
cd infra/     # 加载基础设施规范
```

---

## 关键文档索引

| 文档 | 用途 | 何时读取 |
|------|------|---------|
| [docs/progress.md](../docs/progress.md) | 项目进度追踪 | **每次会话开始** |
| [docs/strategy/roadmap.md](../docs/strategy/roadmap.md) | 四阶段路线图详情 | 规划下一步时 |
| [docs/strategy/product-architecture.md](../docs/strategy/product-architecture.md) | 产品能力模块定义 | 开发新模块时 |
| [docs/strategy/goals-metrics.md](../docs/strategy/goals-metrics.md) | 指标体系和阶段目标 | 评审验收时 |
| [.claude/rules/common.md](.claude/rules/common.md) | 跨项目通用规则 | Git 提交、文档规范 |

### 子项目规范

| 子项目 | 规范入口 |
|--------|---------|
| 后端 | [backend/.claude/CLAUDE.md](../backend/.claude/CLAUDE.md) |
| 前端 | [frontend/.claude/CLAUDE.md](../frontend/.claude/CLAUDE.md) |
| 基础设施 | [infra/.claude/CLAUDE.md](../infra/.claude/CLAUDE.md) |

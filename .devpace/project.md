# AI Agents Platform

> 基于 Amazon Bedrock AgentCore 的企业级 AI Agents 平台，让企业团队能够创建、部署和管理 AI Agent

## 业务目标

### OBJ-1: 构建企业级 AI Agents 平台（product，长期 12 个月）

**成效指标 (MoS)**：
- 企业团队可自助创建和部署 AI Agent
- 平台提供完整的权限管理、审计和成本控制
- 支持知识库集成和工具调用
- Agent 开发到部署周期 < 1 天

**业务需求 (BR)**：
- BR-1: Agent 生命周期（3 PF，P0）→ 详见 requirements/BR-001.md
- BR-2: 对话执行（3 PF，P0）→ 详见 requirements/BR-002.md
- BR-3: 知识增强（1 PF）
- BR-4: 工具集成（1 PF）
- BR-5: 质量评测（3 PF）
- BR-6: 平台治理（4 PF，P1）→ 详见 requirements/BR-006.md
- BR-7: 用户界面（3 PF）

## 战略上下文

### 核心假设
- 企业对 AI Agent 有强烈需求，但缺乏内部平台能力
- Amazon Bedrock AgentCore 能提供可靠的底层 Agent 运行时
- Claude Agent SDK 是当前最适合的 Agent 开发框架

### 外部约束
- 依赖 AWS 云服务，需要企业 AWS 账户
- Agent 执行路径依赖 Claude Code CLI (Node.js)

## 实施路径

（首次 `/pace-plan` 时规划）

## 范围

### 做

- 后端服务 (Python + FastAPI)
- 前端应用 (React + TypeScript)
- 基础设施 (AWS CDK)

### 不做

（首次 /pace-change 或讨论项目范围时填充）

## 项目原则

（首次 /pace-retro 或讨论技术/产品决策时积累）

## 价值功能树

<!-- source: claude, inferred from codebase -->

```
AI Agents Platform (OBJ-1)
│
├── BR-1: Agent 生命周期 [P0] → requirements/BR-001.md
│   ├── PF-01: Agent 管理（CRUD + 状态管理）  [backend:agents, frontend:agents]
│   ├── PF-02: Agent 模板（预设模板库）  [backend:templates, frontend:templates]
│   └── PF-03: Agent 构建器（可视化配置）  [backend:builder, frontend:builder]
│
├── BR-2: 对话执行 [P0] → requirements/BR-002.md
│   ├── PF-04: Agent 对话（消息收发 + SSE 流式）  [backend:execution, frontend:execution]
│   ├── PF-05: 团队协作执行（多 Agent 协同）  [backend:execution, frontend:team-executions]
│   └── PF-06: Chat 对话页面  [frontend:chat]
│
├── BR-3: 知识增强
│   └── PF-07: 知识库管理（创建/上传文档/检索）  [backend:knowledge, frontend:knowledge]
│
├── BR-4: 工具集成
│   └── PF-08: 工具目录（注册/审批/调用）  [backend:tool_catalog, frontend:tool-catalog]
│
├── BR-5: 质量评测
│   ├── PF-09: 测试套件管理（用例编辑）  [backend:evaluation, frontend:evaluation]
│   ├── PF-10: 评测运行（批量评测 + 结果查看）  [backend:evaluation, frontend:evaluation]
│   └── PF-11: 评测 Pipeline（自动化评测流水线）  [backend:evaluation]
│
├── BR-6: 平台治理 [P1] → requirements/BR-006.md
│   ├── PF-12: 用户认证（登录/注册/Token 管理）  [backend:auth, frontend:auth] → CR-001 ⏳
│   ├── PF-13: 审计日志（操作记录查询）  [backend:audit]
│   ├── PF-14: 成本计费（用量统计 + 预算管理）  [backend:billing, frontend:billing]
│   └── PF-15: 使用洞察（数据分析 + 报表）  [backend:insights, frontend:insights]
│
└── BR-7: 用户界面
    ├── PF-16: Dashboard 仪表板  [frontend:dashboard]
    ├── PF-17: Admin 管理页面  [frontend:admin]
    └── PF-18: 用户注册页面  [frontend:register]
```

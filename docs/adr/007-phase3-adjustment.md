# ADR-007: Phase 3 路线图调整 — 基于 Phase 2 开发经验

- **日期**: 2026-02-11
- **状态**: 已采纳
- **关联**: ADR-006 (Agent 框架选型), C-S3-3 (路线图调整评审)
- **来源**: improvement-plan.md 产品审查 P1+P3+P10

## 背景

### Phase 2 完成状态

Phase 2 后端 8 个模块全部完成（shared, auth, agents, execution, tool-catalog, knowledge, insights, templates），1427 测试通过，覆盖率 > 94%。5/5 CDK Stack 部署成功（Network, Security, Database, AgentCore, Compute）。

### 需要解决的问题

improvement-plan.md 产品审查提出以下质疑：

1. **P1**: 24 个月路线图在 AI 快速迭代时代是否过长？
2. **P3**: knowledge 模块排序合理性（已在 Phase 2 调整完毕）
3. **P4**: 用户增长假设（200 人）缺乏依据
4. **P8**: Phase 4 自助式创建比例 60% 假设乐观
5. **P9**: marketplace 对内部平台的必要性
6. **P10**: 竞争分析未融入路线图决策
7. **D9**: 灾备目标 (RPO<1s, RTO<1min) 对内部平台过于激进

### Phase 2 实际经验

开发过程中发现的关键问题对 Phase 3 规划有直接影响：

- **AgentCore 集成进度**: P0+P1 完成 (10/16)，但 P2/P3 还有 6 项未开始
- **S4 运维基础**: CI/CD、Secrets 管理、监控告警均未完成
- **MySQL 兼容性**: 5+ 方言差异导致多次部署失败
- **容器化部署**: ARM64/AMD64、Docker Hub 限流、健康检查工具等问题

## 决策

### 1. 总体时间缩短: 24 月 → 18 月

将固定 24 个月路线图转换为滚动规划模式：
- Phase 3（当前）: 详细规划到周
- Phase 4: 方向性规划，季度评审时细化
- 建立每 12 周季度评审机制

### 2. Phase 3 新增 M7-prep 里程碑

在 orchestration 模块之前，新增 4 周准备期集中完成：
- AgentCore P2 集成 (Gateway 工具同步 + Memory MCP + OTEL)
- 剩余 S4 变更 (CI/CD + Secrets + 监控告警)

### 3. Phase 4 范围缩减

| 移除/降级 | 理由 |
|-----------|------|
| marketplace 模块 | 200 人内部平台无需市场机制；模板分享通过 templates 模块已满足 |
| analytics 独立模块 | 降级为 insights 模块增强，避免过度工程化 |
| 多区域部署 | 内部平台用户量不支撑多区域 ROI |
| 金融级灾备 (RPO<1s) | 内部平台调整为 RPO<5min, RTO<15min |

### 4. 用户增长目标调整

| 阶段 | 原目标 | 调整后 | 理由 |
|------|--------|--------|------|
| Phase 3 | 50 人 | 20 人 | 初期推广的务实目标 |
| Phase 4 | 200 人 | 50 人 | 阶段性增长更合理 |

### 5. evaluation 模块简化

初期不依赖 AgentCore Evaluations（预览版，API 不稳定），自建轻量评估框架（测试集 + 批量执行 + 评分）。AgentCore Evaluations GA 后可平滑切换。

## 理由

### 24 月路线图过长

AI 领域在 2025-2026 年变化极快（AgentCore GA、Claude Agent SDK 快速迭代、MCP 协议标准化）。Phase 4 中规划的 marketplace 和多区域部署，到 12 个月后技术方案可能已完全不同。滚动规划 + 季度评审可保持灵活性。

### Phase 2 经验教训

Phase 2 五维度审查发现 64 项问题，证明"先快速开发后集中修复"模式有效但耗时。Phase 3 技术债务预算从 20% 上调到 25%，并在 M7-prep 中集中处理遗留项，避免带着技术债进入 orchestration 复杂模块。

### 内部平台定位

项目定位为"企业内部 AI Agents 平台"，200 人以内的用户规模不需要：
- 市场机制（marketplace）: 内部团队间分享 Agent 通过 templates 模块 + 内部沟通即可
- 多区域部署: 单区域 + 跨 AZ 高可用已满足内部平台 SLA
- 金融级灾备: RPO<5min, RTO<15min 对内部平台已足够

## 影响

### 对 roadmap.md 的修改

1. Phase 3 新增 M7-prep 里程碑（第 25-28 周）
2. Phase 3 验收标准新增 AgentCore 集成覆盖和运维成熟度
3. Phase 4 时间窗口从 12-24 月缩短至 12-18 月
4. Phase 4 移除 marketplace 模块和多区域部署
5. Phase 4 analytics 降级为 insights 增强
6. 灾备指标调整为 RPO<5min, RTO<15min
7. 新增 Phase 2 经验教训节
8. 新增季度评审机制（§8.3）
9. 技术债务预算 Phase 3 从 20% 调整为 25%

### 对 agentcore-integration-plan.md 的影响

P2 行动项的时间窗口明确为 M7-prep（第 25-28 周），不再是模糊的"Phase 3 之前"。

### 后端模块总数调整

| 阶段 | 原规划模块数 | 调整后 |
|------|:-----------:|:------:|
| Phase 1 | 4 | 4（不变） |
| Phase 2 | 4 | 4（不变） |
| Phase 3 | 2 | 2（不变） |
| Phase 4 | 3 (audit + marketplace + analytics) | **1** (audit) + insights 增强 |
| **总计** | **13** | **11** |

### 对团队的影响

- Phase 3 前 4 周专注基础设施和集成，非业务模块开发
- Phase 4 工作量大幅缩减，可将精力集中在 audit 质量和平台推广
- 季度评审需要产品和技术团队共同参与

## 替代方案

### 保持原 24 月规划不变

**不选原因**: Phase 4 中 marketplace + 多区域 + 金融级灾备的工作量大，但对 200 人内部平台的边际价值低。保持原规划会导致 Phase 4 中大量工程投入的 ROI 不成正比。

### 完全放弃 Phase 4 规划

**不选原因**: audit 模块对企业合规仍是必须的；insights 增强和自助构建器对降低使用门槛有实际价值。完全放弃会缺乏方向性指引。

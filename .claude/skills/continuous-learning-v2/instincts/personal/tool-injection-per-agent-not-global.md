---
id: tool-injection-per-agent-not-global
trigger: "when loading tools for Agent execution"
confidence: 0.9
domain: "agent-runtime"
source: "session-observation-2026-02-28"
---

# 工具注入必须按 Agent 绑定过滤，禁止全平台注入

## Action
`_get_agent_tools(agent_id)` 必须传入 agent_id 并调用 `list_tools_for_agent(agent_id)`，
而非 `list_approved_tools()` 返回全平台所有已审批工具。

## Evidence
- 2026-02-28: `list_approved_tools()` 返回全平台 39 个工具 (37 api + 2 mcp_server)
- 2 个 mcp_server 触发 gateway SSE 连接 → CLI 崩溃
- Agent 实际配置了 0 个工具，但收到 39 个
- Teams 路径不调用 _get_agent_tools 所以不受影响

## Pattern
跨模块查询接口的粒度必须匹配消费方需求:
- list_approved_tools() → 管理后台展示用
- list_tools_for_agent(id) → Agent 执行用

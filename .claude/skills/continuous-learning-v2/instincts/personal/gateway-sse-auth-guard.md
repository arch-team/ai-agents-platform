---
id: gateway-sse-auth-guard
trigger: "when configuring MCP SSE server for CLI subprocess"
confidence: 0.9
domain: "agent-runtime"
source: "session-observation-2026-02-28"
---

# Gateway SSE MCP 必须有认证才能注入 CLI

## Action
配置 SSE 类型 MCP Server 给 CLI 子进程前，必须验证 auth token 存在。
无 token 时跳过注入并记录 warning，防止 CLI 401 崩溃。

## Evidence
- 2026-02-28: AgentCore Gateway 返回 401 "Missing Bearer token"
- CLI 收到 401 → MCP 初始化失败 → 进程退出 → stdio pipe 断裂
- ProcessTransport is not ready for writing → CLIConnectionError
- CLI 是编译的 Node.js SEA 二进制，无法修改其 MCP 初始化容错

## Pattern
```
CLI 子进程对 MCP 初始化失败的容错很差 (直接 crash)
→ 必须在 Python 适配器层做前置验证
→ 不发送 "注定失败" 的 MCP 配置给 CLI
```

---
id: cdk-context-default-hierarchy
trigger: "when CDK stack props have default values that differ from bin/app.ts context defaults"
confidence: 0.8
domain: "infrastructure"
source: "session-observation-2026-02-28"
---

# CDK Context 默认值层级: bin/app.ts 覆盖 Stack Props

## Action
`bin/app.ts` 的 `tryGetContext() ?? 'default'` 会覆盖 `compute-stack.ts` 的 `props.xxx ?? 'other_default'`。
实际生效的是入口文件的默认值，Stack Props 默认值形同虚设。

## Evidence
- 2026-02-28: compute-stack.ts 默认 `in_process`，bin/app.ts 默认 `agentcore_runtime`
- CDK deploy 不带 --context 时实际为 agentcore_runtime
- 需要显式 `--context agentRuntimeMode=in_process` 才能切换

# 变更请求工作流

> **职责**：定义本项目变更请求的状态机。

## 状态流转

```
created → developing → verifying → in_review → approved → merged
              ↑            │              │
              └────────────┘              │
              └───────────────────────────┘

          任何状态 ⇄ paused（暂停/恢复，工作成果保留）
```

## 阶段规则

### created → developing

- 必须关联一个产品功能
- 必须指定目标应用
- Claude 完成意图检查点

### developing → verifying（Claude 自治）

准出条件（具体检查项见 checks.md）：
- [ ] 代码提交到 feature branch
- [ ] 项目质量检查全部通过

### verifying → in_review（Claude 自治）

准出条件（具体检查项见 checks.md）：
- [ ] 集成测试通过
- [ ] 项目质量检查全部通过

### in_review → approved（人类审批）

> Claude 必须停下，生成变更摘要，等待人类 review。

### approved → merged（Claude 执行）

合并后必须执行连锁更新：
1. 更新 PF 状态
2. 更新 project.md 价值功能树
3. 更新 state.md

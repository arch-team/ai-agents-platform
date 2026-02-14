# Onboarding 流程

> AI Agents Platform 新用户入职引导

---

## 概述

本目录包含面向不同角色的入职培训材料，确保新用户能快速上手平台。

## 目录结构

| 文件 | 受众 | 内容 |
|------|------|------|
| [developer-onboarding.md](developer-onboarding.md) | DEVELOPER 角色 | 开发者快速上手指南 |
| [admin-onboarding.md](admin-onboarding.md) | ADMIN 角色 | 管理员操作指南 |
| [viewer-onboarding.md](viewer-onboarding.md) | VIEWER 角色 | 只读用户入门 |
| [faq.md](faq.md) | 所有用户 | 常见问题解答 |

## Onboarding 流程

### 第一天：账户设置

1. 联系管理员获取账户（或通过注册端点自助注册）
2. 登录平台，完成密码设置
3. 浏览 Dashboard 了解平台概况
4. 阅读 [快速入门](../user-guide/quick-start.md)

### 第一周：核心功能

| 天数 | 学习内容 | 参考文档 |
|------|---------|---------|
| Day 1-2 | 创建第一个 Agent，配置 System Prompt | [Agent 管理指南](../user-guide/agent-management.md) |
| Day 3 | 与 Agent 进行对话，了解 SSE 流式响应 | [快速入门](../user-guide/quick-start.md) |
| Day 4 | 注册工具到工具目录（DEVELOPER） | [工具集成指南](../user-guide/tool-integration.md) |
| Day 5 | 创建知识库，上传文档 | [知识库使用指南](../user-guide/knowledge-base.md) |

### 第二周：进阶功能

| 天数 | 学习内容 | 参考文档 |
|------|---------|---------|
| Day 6-7 | 使用模板快速创建专业 Agent | [模板使用指南](../user-guide/templates.md) |
| Day 8 | 探索 Agent Teams 多智能体协作 | [Agent 管理指南](../user-guide/agent-management.md) |
| Day 9-10 | 查看使用洞察和成本数据 | [平台运维](../admin-guide/platform-operations.md) |

## 反馈渠道

如果在使用中遇到问题或有改进建议，请通过以下方式反馈：

1. **GitHub Issues**: 在项目仓库提交 Issue
2. **平台内反馈**: 通过 Dashboard 右下角的反馈按钮
3. **直接联系**: 发送邮件至平台管理员

## 反馈模板

### Bug 报告模板

```markdown
## Bug 描述
[简要描述问题]

## 复现步骤
1.
2.
3.

## 期望行为
[描述期望的正确行为]

## 实际行为
[描述实际发生的错误行为]

## 环境信息
- 浏览器:
- 操作系统:
- 账户角色: ADMIN / DEVELOPER / VIEWER
```

### 功能建议模板

```markdown
## 功能描述
[描述期望的新功能]

## 使用场景
[描述在什么场景下需要这个功能]

## 当前替代方案
[如果有的话，描述当前如何实现类似功能]

## 优先级建议
- [ ] 高 - 影响日常使用
- [ ] 中 - 提升效率
- [ ] 低 - 锦上添花
```

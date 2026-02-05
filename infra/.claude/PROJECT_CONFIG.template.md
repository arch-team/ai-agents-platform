# 项目配置模板 (Project Configuration Template)

<!--
使用说明：
1. 复制此模板到新项目的 .claude/ 目录
2. 替换所有 {{PLACEHOLDER}} 占位符
3. 删除不适用的章节
4. 保持与 CLAUDE.md 的单向引用（CLAUDE.md → PROJECT_CONFIG.md）
-->

> **定位**: 本文件是 CLAUDE.md 的补充，包含**项目特定的业务配置**。
> **原则**: 通用规范放 `rules/`，项目特定信息放此处。
> 架构规范详见 [rules/architecture.md](rules/architecture.md)

---

## 项目信息

<!-- 替换为实际项目信息 -->
| 配置项 | 值 |
|--------|-----|
| **项目名称** | {{PROJECT_NAME}} |
| **项目描述** | {{PROJECT_DESCRIPTION}} |
| **架构模式** | CDK Construct 分层 (L1 → L2 → L3) |
| **CDK 版本** | >=2.130.0 |
| **Node 版本** | >=18.0.0 |
| **源码根路径** | `lib` |

---

## 技术栈补充

> **注意**: 核心技术栈定义在 CLAUDE.md，此处仅列出**项目特有**的技术选型。

| 类别 | 技术选型 | 用途说明 |
|------|---------|---------|
| **数据库** | {{DATABASE}} | {{DATABASE_PURPOSE}} |
| **消息队列** | {{QUEUE}} | {{QUEUE_PURPOSE}} |
<!-- 添加其他项目特有技术 -->

---

## Stack 列表

Stack 设计规范和职责说明见 [architecture.md §2.1](rules/architecture.md#21-stack-职责)

**本项目 Stack**: 根据实际需求填写

---

## 环境配置

> **设计原则**: 使用 CDK Context 管理不同环境的配置。

### 环境定义

| 环境 | AWS 账户 | Region | 用途 |
|------|---------|--------|------|
| `dev` | {{DEV_ACCOUNT}} | {{REGION}} | 开发测试 |
| `staging` | {{STAGING_ACCOUNT}} | {{REGION}} | 预发布验证 |
| `prod` | {{PROD_ACCOUNT}} | {{REGION}} | 生产环境 |

### CDK Context 配置

详细配置示例见 [deployment.md §1.1](rules/deployment.md#11-cdk-context)

---

## Construct 列表

> **位置约定**: 自定义 Construct 放在 `lib/constructs/` 下。

| Construct | 职责 | 组合资源 |
|-----------|------|---------|
| `VpcConstruct` | VPC 配置 | VPC, Subnets, NAT Gateway |
| `{{CONSTRUCT_1}}` | {{CONSTRUCT_1_DESC}} | {{RESOURCES}} |

---

## 命名约定

命名规范见 [CLAUDE.md §命名规范](../CLAUDE.md#命名规范)

**本项目前缀**: `{{PROJECT_PREFIX}}`

---

## 架构合规规则

> **详细规则**: 见 [rules/security.md](rules/security.md) 和 [rules/architecture.md](rules/architecture.md)

### CDK Nag 检查

```typescript
// bin/app.ts
import { Aspects } from 'aws-cdk-lib';
import { AwsSolutionsChecks } from 'cdk-nag';

Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
```

---

## 成本标签

```typescript
const requiredTags = {
  Project: '{{PROJECT_NAME}}',
  Environment: env,
  ManagedBy: 'cdk',
  CostCenter: '{{COST_CENTER}}',
};
```

---

## 模板使用检查清单

在使用此模板创建新项目配置时：

- [ ] 替换所有 `{{PLACEHOLDER}}` 占位符
- [ ] 删除不适用的章节和注释
- [ ] 确保 CLAUDE.md 引用此文件
- [ ] 配置 cdk.json 环境上下文

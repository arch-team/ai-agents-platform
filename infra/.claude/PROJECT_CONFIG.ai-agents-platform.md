# 项目配置 - AI Agents Platform Infrastructure

> **定位**: 本文件是 CLAUDE.md 的补充，包含**项目特定的业务配置**。
> **原则**: 通用规范放 `rules/`，项目特定信息放此处。
> 架构规范详见 [rules/architecture.md](rules/architecture.md)

---

## 项目信息

| 配置项 | 值 |
|--------|-----|
| **项目名称** | ai-agents-platform-infra |
| **项目描述** | AI Agents Platform - 企业级 AI Agents 平台基础设施 |
| **架构模式** | CDK Construct 分层 (L1 → L2 → L3) |
| **CDK 版本** | >=2.130.0 |
| **Node 版本** | >=18.0.0 |
| **源码根路径** | `lib` |

---

## 技术栈补充

> **注意**: 核心技术栈定义在 CLAUDE.md，此处列出版本要求和项目特有选型。

| 类别 | 技术选型 | 版本要求 |
|------|---------|---------|
| **IaC** | AWS CDK | >=2.130.0 |
| **测试** | Jest | >=29.0.0 |
| **CDK 断言** | aws-cdk-lib/assertions | - |
| **安全检查** | cdk-nag | >=2.28.0 |
| **构造库** | @aws-cdk/aws-* | - |

---

## Stack 列表

Stack 设计规范见 [architecture.md §2.1](rules/architecture.md#21-stack-职责)

**本项目 Stack**:

| Stack | 依赖 |
|-------|------|
| `NetworkStack` | - |
| `SecurityStack` | NetworkStack |
| `DatabaseStack` | NetworkStack, SecurityStack |
| `ComputeStack` | NetworkStack, SecurityStack |
| `ApiStack` | ComputeStack |
| `MonitoringStack` | All Stacks |

---

## 环境配置

> **设计原则**: 使用 CDK Context 管理不同环境的配置。

### 环境定义

| 环境 | AWS 账户 | Region | 用途 |
|------|---------|--------|------|
| `dev` | 123456789012 | ap-northeast-1 | 开发测试 |
| `staging` | 123456789013 | ap-northeast-1 | 预发布验证 |
| `prod` | 123456789014 | ap-northeast-1 | 生产环境 |

### CDK Context 配置

详细配置结构见 [deployment.md §1.1](rules/deployment.md#11-cdk-context)

**本项目配置值**: 见上方环境表格

---

## Construct 列表

> **位置约定**: 自定义 Construct 放在 `lib/constructs/` 下。

| Construct | 职责 | 组合资源 |
|-----------|------|---------|
| `VpcConstruct` | VPC 配置 | VPC, Subnets, NAT Gateway |
| `AuroraConstruct` | Aurora 数据库 | Aurora Cluster, Secret, Security Group |
| `EcsServiceConstruct` | ECS 服务 | ECS Service, Task Definition, ALB Target Group |
| `ApiGatewayConstruct` | API 网关 | REST API, Authorizer, Usage Plan |
| `LambdaConstruct` | Lambda 函数 | Lambda, IAM Role, CloudWatch Logs |

---

## 命名约定

命名规范见 [CLAUDE.md §命名规范](../CLAUDE.md#命名规范)

**本项目前缀**: `ai-platform`
**Stack 命名**: `AiPlatform{Resource}Stack-{env}`

---

## 架构合规规则

> **详细规则**: 见 [rules/security.md](rules/security.md) 和 [rules/architecture.md](rules/architecture.md)

### CDK Nag 检查

```typescript
// bin/app.ts
import { Aspects } from 'aws-cdk-lib';
import { AwsSolutionsChecks } from 'cdk-nag';

// 应用 AWS Solutions 检查
Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
```

### 违规检测

| 违规类型 | 规则 | 严重级别 |
|---------|------|---------|
| 公开 S3 Bucket | AwsSolutions-S3 | 🔴 阻止 |
| 过宽 IAM 权限 | AwsSolutions-IAM4 | 🔴 阻止 |
| 未加密存储 | AwsSolutions-RDS10 | 🟡 警告 |
| 缺少访问日志 | AwsSolutions-ELB2 | 🟡 警告 |

---

## 成本标签

> **原则**: 所有资源必须包含成本标签用于成本分配。

```typescript
// 必须的标签
const requiredTags = {
  Project: 'ai-agents-platform',
  Environment: env,
  ManagedBy: 'cdk',
  CostCenter: 'ai-platform',
};

// 应用标签
Tags.of(app).add('Project', 'ai-agents-platform');
Tags.of(app).add('Environment', env);
```

---

## PR Review 检查清单

- [ ] 新 Stack 已添加到 Stack 列表
- [ ] 资源命名符合约定
- [ ] CDK Nag 检查通过
- [ ] 成本标签已配置
- [ ] 包含对应的测试文件
- [ ] 敏感信息使用 Secrets Manager

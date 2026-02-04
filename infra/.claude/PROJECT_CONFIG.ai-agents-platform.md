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

> **维护提示**: 新增 Stack 时同步更新此表和 `lib/stacks/` 目录。

| Stack | 职责 | 核心资源 | 依赖 |
|-------|------|---------|------|
| `NetworkStack` | 网络基础设施 | VPC, Subnets, NAT Gateway | - |
| `SecurityStack` | 安全组和 IAM | Security Groups, IAM Roles | NetworkStack |
| `DatabaseStack` | 数据库 | Aurora MySQL, ElastiCache | NetworkStack, SecurityStack |
| `ComputeStack` | 计算资源 | ECS/Fargate, Lambda | NetworkStack, SecurityStack |
| `ApiStack` | API 网关 | API Gateway, WAF | ComputeStack |
| `MonitoringStack` | 监控告警 | CloudWatch, SNS | All Stacks |
<!-- 示例：
| `StorageStack` | 存储资源 | S3, EFS | NetworkStack |
| `CiCdStack` | CI/CD Pipeline | CodePipeline, CodeBuild | - |
-->

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

```typescript
// cdk.json
{
  "context": {
    "environments": {
      "dev": {
        "account": "123456789012",
        "region": "ap-northeast-1",
        "vpcCidr": "10.0.0.0/16",
        "instanceType": "t3.small",
        "minCapacity": 1,
        "maxCapacity": 2
      },
      "staging": {
        "account": "123456789013",
        "region": "ap-northeast-1",
        "vpcCidr": "10.1.0.0/16",
        "instanceType": "t3.medium",
        "minCapacity": 2,
        "maxCapacity": 4
      },
      "prod": {
        "account": "123456789014",
        "region": "ap-northeast-1",
        "vpcCidr": "10.2.0.0/16",
        "instanceType": "t3.large",
        "minCapacity": 3,
        "maxCapacity": 10
      }
    }
  }
}
```

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

> **原则**: 资源命名包含环境和项目前缀，便于识别和管理。

### 资源命名模式

```typescript
// 格式: {project}-{env}-{resource-type}-{name}
const naming = {
  vpc: `ai-platform-${env}-vpc`,
  cluster: `ai-platform-${env}-aurora`,
  service: `ai-platform-${env}-api-service`,
  lambda: `ai-platform-${env}-auth-handler`,
};
```

### Stack 命名

```typescript
// 格式: {Project}{Resource}Stack-{env}
new NetworkStack(app, `AiPlatformNetworkStack-${env}`, { ... });
new ComputeStack(app, `AiPlatformComputeStack-${env}`, { ... });
```

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

# CDK 架构规范 (CDK Architecture Standards)

> **版本**: 1.0
> **架构模式**: CDK Construct 分层 (L1 → L2 → L3)
> **适用范围**: AWS CDK TypeScript 项目

本文档是 CDK 项目的**核心架构规范单一真实源 (Single Source of Truth)**。

<!-- CLAUDE: 项目特定配置请参考 PROJECT_CONFIG.ai-agents-platform.md -->

<!-- CLAUDE 占位符说明:
  {Stack}      → Stack 名称 PascalCase，如 Network, Compute, Api
  {Construct}  → Construct 名称 PascalCase，如 Vpc, Aurora, EcsService
  {construct}  → Construct 名称 kebab-case，如 vpc, aurora, ecs-service
  {Resource}   → AWS 资源类型，如 VPC, Lambda, S3
  {env}        → 环境名称，如 dev, staging, prod
-->

---

## 0. 速查卡片

> Claude 生成代码时优先查阅此章节

### 0.1 Construct 层级速查

| 层级 | 描述 | 来源 | 示例 |
|------|------|------|------|
| **L1** | CloudFormation 资源直接映射 | `Cfn*` 前缀类 | `CfnBucket`, `CfnFunction` |
| **L2** | 高级抽象，含合理默认值 | `aws-*` 模块 | `s3.Bucket`, `lambda.Function` |
| **L3** | 业务组合，多资源协作 | 自定义 Construct | `VpcConstruct`, `ApiGatewayConstruct` |

### 0.2 依赖方向

```
App
 │
 ├── Stack A ────────────────────┐
 │    ├── L3 Construct          │ 依赖
 │    │    └── L2 Construct     │
 │    │         └── L1 (Cfn*)   │
 │    └── ...                   │
 │                              ▼
 └── Stack B (依赖 Stack A 的输出)
```

**核心规则**:
- Stack 之间通过输出值 (Outputs) 传递依赖
- Construct 内部从高层调用低层
- 禁止循环依赖

### 0.3 Stack 组合模式

| 模式 | 适用场景 | 示例 |
|------|---------|------|
| **按资源类型** | 资源生命周期不同 | NetworkStack, ComputeStack, DatabaseStack |
| **按环境** | 多环境部署 | dev-Stack, staging-Stack, prod-Stack |
| **按服务** | 微服务架构 | AuthStack, AgentStack, MonitoringStack |

### 0.4 PR Review 检查清单

**分层规则**:
- [ ] 自定义 Construct 放在 `lib/constructs/`
- [ ] Stack 放在 `lib/stacks/`
- [ ] 没有跨 Stack 的直接资源引用

**Construct 设计**:
- [ ] Props 使用 `readonly` 修饰
- [ ] 有合理的默认值
- [ ] 暴露必要的属性供外部使用

**安全检查**:
- [ ] CDK Nag 检查通过
- [ ] 敏感信息使用 Secrets Manager
- [ ] IAM 权限使用 Grant 方法

---

## 1. CDK Construct 分层

### 1.1 L1 - CloudFormation 资源

**特点**: 与 CloudFormation 资源一一对应，无抽象

```typescript
// ❌ 通常不直接使用 L1，除非 L2 不支持某功能
import { CfnBucket } from 'aws-cdk-lib/aws-s3';

const cfnBucket = new CfnBucket(this, 'MyCfnBucket', {
  bucketName: 'my-bucket',
  versioningConfiguration: {
    status: 'Enabled',
  },
});
```

### 1.2 L2 - 高级 Construct

**特点**: 提供合理默认值、类型安全、Grant 方法

```typescript
// ✅ 优先使用 L2 Construct
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';

const bucket = new s3.Bucket(this, 'DataBucket', {
  versioned: true,
  encryption: s3.BucketEncryption.S3_MANAGED,
  removalPolicy: cdk.RemovalPolicy.RETAIN,
});

const fn = new lambda.Function(this, 'Handler', {
  runtime: lambda.Runtime.NODEJS_18_X,
  handler: 'index.handler',
  code: lambda.Code.fromAsset('lambda'),
});

// 使用 Grant 方法授权
bucket.grantRead(fn);
```

### 1.3 L3 - 自定义 Construct

**特点**: 组合多个资源，封装业务模式

```typescript
// lib/constructs/api-gateway/api-gateway.construct.ts
import { Construct } from 'constructs';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';
import * as logs from 'aws-cdk-lib/aws-logs';

export interface ApiGatewayConstructProps {
  readonly stageName: string;
  readonly throttlingRateLimit?: number;
  readonly enableAccessLogs?: boolean;
  readonly enableWaf?: boolean;
}

export class ApiGatewayConstruct extends Construct {
  public readonly api: apigateway.RestApi;
  public readonly logGroup?: logs.LogGroup;

  constructor(scope: Construct, id: string, props: ApiGatewayConstructProps) {
    super(scope, id);

    const { stageName, throttlingRateLimit = 1000, enableAccessLogs = true, enableWaf = true } = props;

    // 访问日志
    if (enableAccessLogs) {
      this.logGroup = new logs.LogGroup(this, 'AccessLogs', {
        retention: logs.RetentionDays.ONE_MONTH,
      });
    }

    // API Gateway
    this.api = new apigateway.RestApi(this, 'Api', {
      restApiName: `${id}-api`,
      deployOptions: {
        stageName,
        throttlingRateLimit,
        accessLogDestination: this.logGroup
          ? new apigateway.LogGroupLogDestination(this.logGroup)
          : undefined,
      },
    });

    // WAF
    if (enableWaf) {
      this.attachWaf();
    }
  }

  private attachWaf(): void {
    // WAF 配置
    const webAcl = new wafv2.CfnWebACL(this, 'WebAcl', {
      scope: 'REGIONAL',
      defaultAction: { allow: {} },
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: 'ApiWaf',
      },
      rules: [],
    });

    new wafv2.CfnWebACLAssociation(this, 'WebAclAssociation', {
      resourceArn: this.api.deploymentStage.stageArn,
      webAclArn: webAcl.attrArn,
    });
  }
}
```

---

## 2. Stack 设计

### 2.1 Stack 职责

每个 Stack 应该有单一、明确的职责：

| Stack | 职责 | 包含资源 |
|-------|------|---------|
| NetworkStack | 网络基础设施 | VPC, Subnets, NAT, VPN |
| SecurityStack | 安全配置 | Security Groups, WAF, KMS |
| DatabaseStack | 数据存储 | RDS, DynamoDB, ElastiCache |
| ComputeStack | 计算资源 | ECS, Lambda, EC2 |
| ApiStack | API 层 | API Gateway, ALB |
| MonitoringStack | 监控告警 | CloudWatch, SNS, Alarms |

### 2.2 Stack 间依赖

```typescript
// bin/app.ts
import * as cdk from 'aws-cdk-lib';
import { NetworkStack } from '../lib/stacks/network-stack';
import { ComputeStack } from '../lib/stacks/compute-stack';

const app = new cdk.App();
const env = app.node.tryGetContext('env') || 'dev';

// 创建网络 Stack
const networkStack = new NetworkStack(app, `NetworkStack-${env}`, {
  env: { account: '123456789012', region: 'ap-northeast-1' },
});

// Compute Stack 依赖 Network Stack
const computeStack = new ComputeStack(app, `ComputeStack-${env}`, {
  env: { account: '123456789012', region: 'ap-northeast-1' },
  vpc: networkStack.vpc, // 通过 props 传递
});

// 声明显式依赖
computeStack.addDependency(networkStack);
```

### 2.3 Stack Props 设计

```typescript
// lib/stacks/compute-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';

export interface ComputeStackProps extends cdk.StackProps {
  readonly vpc: ec2.IVpc;
  readonly instanceType?: ec2.InstanceType;
  readonly minCapacity?: number;
  readonly maxCapacity?: number;
}

export class ComputeStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    super(scope, id, props);

    const {
      vpc,
      instanceType = ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.SMALL),
      minCapacity = 1,
      maxCapacity = 10,
    } = props;

    // 使用传入的 VPC
    // ...
  }
}
```

---

## 3. 目录结构

```
infra/
├── bin/
│   └── app.ts                 # CDK 应用入口
├── lib/
│   ├── constructs/            # 自定义 L3 Construct
│   │   ├── vpc/
│   │   │   ├── index.ts
│   │   │   ├── vpc.construct.ts
│   │   │   └── vpc.construct.test.ts
│   │   ├── aurora/
│   │   │   ├── index.ts
│   │   │   ├── aurora.construct.ts
│   │   │   └── aurora.construct.test.ts
│   │   └── api-gateway/
│   │       └── ...
│   ├── stacks/                # Stack 定义
│   │   ├── network-stack.ts
│   │   ├── compute-stack.ts
│   │   └── api-stack.ts
│   └── config/                # 配置和常量
│       ├── environments.ts
│       └── constants.ts
├── test/                      # 测试文件
│   ├── constructs/
│   │   └── vpc.construct.test.ts
│   └── stacks/
│       └── network-stack.test.ts
├── cdk.json                   # CDK 配置
├── package.json
└── tsconfig.json
```

---

## 4. 跨 Stack 通信

### 4.1 使用 Stack Props

```typescript
// 推荐：通过 Props 传递
const networkStack = new NetworkStack(app, 'NetworkStack');
const computeStack = new ComputeStack(app, 'ComputeStack', {
  vpc: networkStack.vpc,
});
```

### 4.2 使用 SSM Parameter

```typescript
// 写入参数 (Network Stack)
new ssm.StringParameter(this, 'VpcIdParam', {
  parameterName: '/infra/network/vpc-id',
  stringValue: this.vpc.vpcId,
});

// 读取参数 (Compute Stack)
const vpcId = ssm.StringParameter.valueFromLookup(this, '/infra/network/vpc-id');
const vpc = ec2.Vpc.fromLookup(this, 'Vpc', { vpcId });
```

### 4.3 使用 Exports

```typescript
// 导出 (Network Stack)
new cdk.CfnOutput(this, 'VpcIdOutput', {
  value: this.vpc.vpcId,
  exportName: 'NetworkVpcId',
});

// 导入 (Compute Stack)
const vpcId = cdk.Fn.importValue('NetworkVpcId');
```

---

## 5. 环境配置

### 5.1 CDK Context

```typescript
// lib/config/environments.ts
export interface EnvironmentConfig {
  readonly account: string;
  readonly region: string;
  readonly vpcCidr: string;
  readonly instanceType: string;
}

export function getEnvironmentConfig(app: cdk.App, envName: string): EnvironmentConfig {
  const environments = app.node.tryGetContext('environments');
  const config = environments?.[envName];

  if (!config) {
    throw new Error(`未找到环境配置: ${envName}`);
  }

  return config as EnvironmentConfig;
}
```

### 5.2 使用环境配置

```typescript
// bin/app.ts
const envName = app.node.tryGetContext('env') || 'dev';
const envConfig = getEnvironmentConfig(app, envName);

new NetworkStack(app, `NetworkStack-${envName}`, {
  env: { account: envConfig.account, region: envConfig.region },
  vpcCidr: envConfig.vpcCidr,
});
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| `PROJECT_CONFIG.ai-agents-platform.md` | 项目特定配置 (Stack 列表、环境配置) |
| `CLAUDE.md` | TDD 工作流、命令、代码风格 |
| `rules/construct-design.md` | Construct 设计规范 |
| `rules/security.md` | 安全规范 |
| `rules/testing.md` | 测试规范 |

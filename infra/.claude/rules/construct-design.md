# Construct 设计规范 (Construct Design Standards)

> Claude 生成 CDK Construct 代码时优先查阅此文档

---

## 0. 速查卡片

### Props 设计速查

| 规则 | ✅ 正确 | ❌ 错误 |
|------|--------|--------|
| readonly 修饰 | `readonly vpcCidr: string` | `vpcCidr: string` |
| 可选参数 | `readonly timeout?: number` | `readonly timeout: number \| undefined` |
| 默认值 | 解构时设置默认值 | Props 接口中设置 |
| 接口命名 | `{Construct}Props` | `{Construct}Options` |

### Construct 模板

```typescript
export interface {Construct}Props {
  readonly requiredProp: string;
  readonly optionalProp?: number;
}

export class {Construct} extends Construct {
  public readonly resource: ResourceType;

  constructor(scope: Construct, id: string, props: {Construct}Props) {
    super(scope, id);
    const { requiredProp, optionalProp = 100 } = props;
    // 创建资源...
  }
}
```

### 安全默认值速查

| 资源类型 | 默认配置 |
|---------|---------|
| S3 Bucket | 加密、版本控制、阻止公开访问 |
| RDS | 加密、自动备份、删除保护 |
| Lambda | 最小超时、X-Ray 追踪 |
| API Gateway | 访问日志、节流、CORS |

### PR Review 检查清单

- [ ] Props 使用 `readonly` 修饰
- [ ] 可选参数有合理默认值
- [ ] 暴露必要的公开属性
- [ ] 有 JSDoc 注释说明用途
- [ ] 安全配置使用安全默认值
- [ ] 包含对应的测试文件

---

## 1. Props 接口设计

### 1.1 基本规则

```typescript
// ✅ 正确 - 所有属性使用 readonly
export interface VpcConstructProps {
  readonly vpcCidr: string;
  readonly maxAzs?: number;
  readonly enableNatGateway?: boolean;
}

// ❌ 错误 - 缺少 readonly
export interface VpcConstructProps {
  vpcCidr: string;
  maxAzs?: number;
}
```

### 1.2 继承 CDK Props

```typescript
import * as cdk from 'aws-cdk-lib';

// 继承 Stack Props
export interface NetworkStackProps extends cdk.StackProps {
  readonly vpcCidr: string;
}

// 继承 Construct Props (可选)
export interface DatabaseConstructProps {
  readonly vpc: ec2.IVpc;
  readonly instanceType?: ec2.InstanceType;
  readonly removalPolicy?: cdk.RemovalPolicy;
}
```

### 1.3 复杂类型

```typescript
// 嵌套配置使用接口
export interface AutoScalingConfig {
  readonly minCapacity: number;
  readonly maxCapacity: number;
  readonly targetCpuUtilization?: number;
}

export interface EcsServiceConstructProps {
  readonly vpc: ec2.IVpc;
  readonly autoScaling?: AutoScalingConfig;
}
```

---

## 2. Construct 实现

### 2.1 基本结构

```typescript
// lib/constructs/vpc/vpc.construct.ts
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export interface VpcConstructProps {
  readonly vpcCidr: string;
  readonly maxAzs?: number;
  readonly enableNatGateway?: boolean;
}

/**
 * VPC Construct - 创建标准化的 VPC 网络。
 *
 * @remarks
 * 默认配置:
 * - 3 个可用区
 * - 公有/私有子网
 * - NAT Gateway (可选)
 *
 * @example
 * ```typescript
 * new VpcConstruct(this, 'MainVpc', {
 *   vpcCidr: '10.0.0.0/16',
 * });
 * ```
 */
export class VpcConstruct extends Construct {
  /** 创建的 VPC 实例 */
  public readonly vpc: ec2.Vpc;

  constructor(scope: Construct, id: string, props: VpcConstructProps) {
    super(scope, id);

    // 解构并设置默认值
    const {
      vpcCidr,
      maxAzs = 3,
      enableNatGateway = true,
    } = props;

    // 创建 VPC
    this.vpc = new ec2.Vpc(this, 'Vpc', {
      ipAddresses: ec2.IpAddresses.cidr(vpcCidr),
      maxAzs,
      natGateways: enableNatGateway ? maxAzs : 0,
      subnetConfiguration: [
        {
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24,
        },
        {
          name: 'Private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          cidrMask: 24,
        },
        {
          name: 'Isolated',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          cidrMask: 24,
        },
      ],
    });
  }
}
```

### 2.2 暴露属性

```typescript
export class AuroraConstruct extends Construct {
  /** Aurora 集群 */
  public readonly cluster: rds.DatabaseCluster;

  /** 集群端点 */
  public readonly clusterEndpoint: rds.Endpoint;

  /** 只读端点 */
  public readonly readerEndpoint: rds.Endpoint;

  /** 数据库密钥 (Secrets Manager) */
  public readonly secret: secretsmanager.ISecret;

  constructor(scope: Construct, id: string, props: AuroraConstructProps) {
    super(scope, id);

    this.cluster = new rds.DatabaseCluster(this, 'Cluster', {
      // ...配置
    });

    // 暴露属性
    this.clusterEndpoint = this.cluster.clusterEndpoint;
    this.readerEndpoint = this.cluster.clusterReadEndpoint;
    this.secret = this.cluster.secret!;
  }

  /**
   * 授予读取权限
   */
  public grantDataApiAccess(grantee: iam.IGrantable): iam.Grant {
    return this.cluster.grantDataApiAccess(grantee);
  }
}
```

---

## 3. 安全默认配置

### 3.1 S3 Bucket

```typescript
export class SecureBucketConstruct extends Construct {
  public readonly bucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: SecureBucketProps) {
    super(scope, id);

    this.bucket = new s3.Bucket(this, 'Bucket', {
      // 安全默认配置
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      versioned: true,
      removalPolicy: props.removalPolicy ?? cdk.RemovalPolicy.RETAIN,

      // 可选配置
      bucketName: props.bucketName,
      lifecycleRules: props.lifecycleRules,
    });
  }
}
```

### 3.2 Lambda Function

```typescript
export class SecureLambdaConstruct extends Construct {
  public readonly function: lambda.Function;

  constructor(scope: Construct, id: string, props: SecureLambdaProps) {
    super(scope, id);

    this.function = new lambda.Function(this, 'Function', {
      // 安全默认配置
      runtime: lambda.Runtime.NODEJS_18_X,
      tracing: lambda.Tracing.ACTIVE,
      timeout: props.timeout ?? cdk.Duration.seconds(30),
      memorySize: props.memorySize ?? 256,

      // 必需配置
      handler: props.handler,
      code: props.code,
      environment: props.environment,
    });

    // 最小权限
    if (props.logRetention) {
      new logs.LogGroup(this, 'LogGroup', {
        logGroupName: `/aws/lambda/${this.function.functionName}`,
        retention: props.logRetention,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      });
    }
  }
}
```

### 3.3 RDS/Aurora

```typescript
export class SecureAuroraConstruct extends Construct {
  public readonly cluster: rds.DatabaseCluster;

  constructor(scope: Construct, id: string, props: SecureAuroraProps) {
    super(scope, id);

    this.cluster = new rds.DatabaseCluster(this, 'Cluster', {
      engine: rds.DatabaseClusterEngine.auroraMysql({
        version: rds.AuroraMysqlEngineVersion.VER_3_04_0,
      }),

      // 安全默认配置
      storageEncrypted: true,
      deletionProtection: props.deletionProtection ?? true,
      backup: {
        retention: cdk.Duration.days(props.backupRetentionDays ?? 7),
      },
      iamAuthentication: true,

      // 网络配置
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
      },

      // 实例配置
      writer: rds.ClusterInstance.provisioned('Writer', {
        instanceType: props.instanceType ?? ec2.InstanceType.of(
          ec2.InstanceClass.R6G,
          ec2.InstanceSize.LARGE
        ),
      }),
    });
  }
}
```

---

## 4. 导出模式

### 4.1 index.ts 导出

```typescript
// lib/constructs/vpc/index.ts
export { VpcConstruct } from './vpc.construct';
export type { VpcConstructProps } from './vpc.construct';
```

### 4.2 Construct 桶导出

```typescript
// lib/constructs/index.ts
export * from './vpc';
export * from './aurora';
export * from './api-gateway';
export * from './lambda';
```

---

## 5. JSDoc 注释

### 5.1 Construct 注释

```typescript
/**
 * API Gateway Construct - 创建 REST API 入口。
 *
 * @remarks
 * 功能特性:
 * - 自动配置访问日志
 * - 集成 WAF 防护
 * - 支持自定义域名
 *
 * @example
 * ```typescript
 * const api = new ApiGatewayConstruct(this, 'Api', {
 *   stageName: 'prod',
 *   enableWaf: true,
 * });
 *
 * // 添加资源
 * api.api.root.addResource('users');
 * ```
 */
export class ApiGatewayConstruct extends Construct {
  // ...
}
```

### 5.2 Props 注释

```typescript
export interface ApiGatewayConstructProps {
  /** 部署阶段名称 (如 dev, staging, prod) */
  readonly stageName: string;

  /** API 请求节流限制 (每秒请求数) @default 1000 */
  readonly throttlingRateLimit?: number;

  /** 是否启用访问日志 @default true */
  readonly enableAccessLogs?: boolean;

  /** 是否启用 WAF 防护 @default true */
  readonly enableWaf?: boolean;
}
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [architecture.md](architecture.md) | Construct 分层规则 |
| [security.md](security.md) | 安全配置详细规范 |
| [testing.md](testing.md) | Construct 测试规范 |

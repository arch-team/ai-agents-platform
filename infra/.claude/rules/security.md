# 安全规范 (Security Standards)

> Claude 生成 CDK 代码时优先查阅此文档

基于 AWS Well-Architected Framework 安全支柱的 CDK 安全规范。

> **职责边界**: 本文档关注安全**原理和合规要求**（为什么这样写）。安全配置的**代码模板**详见 [construct-design.md §3](construct-design.md#3-安全默认配置)

---

## 0. 速查卡片

### 安全规则速查表

| 规则 | ❌ 禁止 | ✅ 正确 |
|------|--------|--------|
| IAM 权限 | `PolicyStatement({ actions: ['*'] })` | `bucket.grantRead(role)` |
| 密钥管理 | 硬编码在代码中 | Secrets Manager |
| S3 访问 | 公开访问 | `BlockPublicAccess.BLOCK_ALL` |
| RDS | 公开子网 | `PRIVATE_ISOLATED` 子网 |
| 传输加密 | HTTP | HTTPS + TLS 1.2+ |

### Grant 方法速查

| 资源 | Grant 方法 |
|------|-----------|
| S3 | `grantRead()`, `grantWrite()`, `grantReadWrite()`, `grantDelete()` |
| DynamoDB | `grantReadData()`, `grantWriteData()`, `grantReadWriteData()` |
| Lambda | `grantInvoke()`, `grantInvokeUrl()` |
| KMS | `grantEncrypt()`, `grantDecrypt()`, `grantEncryptDecrypt()` |
| SNS | `grantPublish()`, `grantSubscribe()` |
| SQS | `grantSendMessages()`, `grantConsumeMessages()` |
| Secrets | `grantRead()`, `grantWrite()` |

---

## 1. IAM 最小权限

### 1.1 使用 Grant 方法

```typescript
// ✅ 正确 - 使用 Grant 方法
const bucket = new s3.Bucket(this, 'DataBucket');
const lambdaFn = new lambda.Function(this, 'Handler', { ... });

// 自动创建最小权限策略
bucket.grantRead(lambdaFn);
bucket.grantWrite(lambdaFn);

// ❌ 错误 - 手动创建过宽策略
lambdaFn.addToRolePolicy(new iam.PolicyStatement({
  actions: ['s3:*'],
  resources: ['*'],
}));
```

### 1.2 精细权限控制

```typescript
// ✅ 正确 - 限制资源范围
bucket.grantRead(lambdaFn, 'data/*'); // 仅限 data/ 前缀

// ✅ 正确 - 条件限制
const policy = new iam.PolicyStatement({
  actions: ['s3:GetObject'],
  resources: [bucket.arnForObjects('reports/*')],
  conditions: {
    StringEquals: {
      's3:ExistingObjectTag/Environment': 'prod',
    },
  },
});
```

### 1.3 避免 Admin 权限

```typescript
// ❌ 禁止 - 管理员权限
const role = new iam.Role(this, 'Role', {
  assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
  managedPolicies: [
    iam.ManagedPolicy.fromAwsManagedPolicyName('AdministratorAccess'),
  ],
});

// ✅ 正确 - 最小权限
const role = new iam.Role(this, 'Role', {
  assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
});
bucket.grantRead(role);
table.grantReadWriteData(role);
```

---

## 2. 密钥管理

### 2.1 Secrets Manager

```typescript
// ✅ 正确 - 使用 Secrets Manager
const dbSecret = new secretsmanager.Secret(this, 'DbSecret', {
  secretName: 'prod/db/credentials',
  generateSecretString: {
    secretStringTemplate: JSON.stringify({ username: 'admin' }),
    generateStringKey: 'password',
    excludePunctuation: true,
    passwordLength: 32,
  },
});

// 在 RDS 中使用
const cluster = new rds.DatabaseCluster(this, 'Database', {
  credentials: rds.Credentials.fromSecret(dbSecret),
  // ...
});

// 在 Lambda 中使用
const fn = new lambda.Function(this, 'Handler', {
  environment: {
    SECRET_ARN: dbSecret.secretArn,
  },
});
dbSecret.grantRead(fn);
```

### 2.2 SSM Parameter Store

```typescript
// 非敏感配置使用 SSM Parameter
const configParam = new ssm.StringParameter(this, 'Config', {
  parameterName: '/app/config/api-url',
  stringValue: 'https://api.example.com',
});

// 敏感配置使用 SecureString
const secureParam = new ssm.StringParameter(this, 'SecureConfig', {
  parameterName: '/app/secrets/api-key',
  stringValue: 'placeholder', // 实际值通过控制台或 CLI 更新
  tier: ssm.ParameterTier.STANDARD,
});
```

### 2.3 禁止硬编码

```typescript
// ❌ 禁止 - 硬编码密钥
const fn = new lambda.Function(this, 'Handler', {
  environment: {
    API_KEY: 'sk-1234567890abcdef',
    DB_PASSWORD: 'my-secret-password',
  },
});

// ✅ 正确 - 从 Secrets Manager 读取
const apiKeySecret = secretsmanager.Secret.fromSecretNameV2(
  this, 'ApiKey', 'prod/api-key'
);
const fn = new lambda.Function(this, 'Handler', {
  environment: {
    API_KEY_SECRET_ARN: apiKeySecret.secretArn,
  },
});
apiKeySecret.grantRead(fn);
```

---

## 3. 网络安全

### 3.1 VPC 设计

```typescript
// ✅ 正确 - 分层子网设计
const vpc = new ec2.Vpc(this, 'Vpc', {
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

// 数据库放在隔离子网
const database = new rds.DatabaseCluster(this, 'Database', {
  vpc,
  vpcSubnets: {
    subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
  },
});
```

### 3.2 Security Groups

```typescript
// ✅ 正确 - 最小开放端口
const dbSecurityGroup = new ec2.SecurityGroup(this, 'DbSg', {
  vpc,
  description: 'Security group for Aurora database',
  allowAllOutbound: false, // 禁止所有出站
});

// 仅允许应用服务器访问
dbSecurityGroup.addIngressRule(
  appSecurityGroup,
  ec2.Port.tcp(3306),
  'Allow MySQL from app servers'
);
```

### 3.3 VPC Endpoints

```typescript
// ✅ 正确 - 使用 VPC Endpoints 访问 AWS 服务
vpc.addInterfaceEndpoint('SecretsManagerEndpoint', {
  service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
});

vpc.addGatewayEndpoint('S3Endpoint', {
  service: ec2.GatewayVpcEndpointAwsService.S3,
});
```

---

## 4. 数据加密

### 4.1 S3 加密

```typescript
// ✅ 正确 - 启用加密
const bucket = new s3.Bucket(this, 'DataBucket', {
  encryption: s3.BucketEncryption.S3_MANAGED, // 或 KMS_MANAGED
  enforceSSL: true,
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
});

// 使用 CMK 加密
const key = new kms.Key(this, 'BucketKey', {
  enableKeyRotation: true,
});
const bucket = new s3.Bucket(this, 'SecureBucket', {
  encryption: s3.BucketEncryption.KMS,
  encryptionKey: key,
});
```

### 4.2 RDS 加密

```typescript
// ✅ 正确 - 启用存储加密
const cluster = new rds.DatabaseCluster(this, 'Database', {
  storageEncrypted: true,
  // 可选: 自定义 KMS 密钥
  storageEncryptionKey: key,
});
```

### 4.3 传输加密

```typescript
// ✅ 正确 - 强制 HTTPS
const api = new apigateway.RestApi(this, 'Api', {
  // ...
});

// ALB 强制 HTTPS
const lb = new elbv2.ApplicationLoadBalancer(this, 'ALB', {
  vpc,
  internetFacing: true,
});

const httpsListener = lb.addListener('HttpsListener', {
  port: 443,
  certificates: [certificate],
  sslPolicy: elbv2.SslPolicy.TLS12,
});

// HTTP 重定向到 HTTPS
lb.addListener('HttpListener', {
  port: 80,
  defaultAction: elbv2.ListenerAction.redirect({
    protocol: 'HTTPS',
    port: '443',
    permanent: true,
  }),
});
```

---

## 5. CDK Nag

### 5.1 启用 CDK Nag

```typescript
// bin/app.ts
import { Aspects } from 'aws-cdk-lib';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';

const app = new cdk.App();

// 应用 AWS Solutions 检查
Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
```

### 5.2 抑制规则

```typescript
// 仅在有正当理由时抑制
NagSuppressions.addStackSuppressions(stack, [
  {
    id: 'AwsSolutions-IAM4',
    reason: '使用 AWS 托管策略是此用例的最佳实践',
  },
]);

// 资源级抑制
NagSuppressions.addResourceSuppressions(bucket, [
  {
    id: 'AwsSolutions-S1',
    reason: '此 Bucket 用于 CloudTrail 日志，不需要访问日志',
  },
]);
```

### 5.3 常见规则

| 规则 ID | 描述 | 修复方法 |
|---------|------|---------|
| AwsSolutions-S1 | S3 Bucket 应启用访问日志 | 添加 `serverAccessLogsBucket` |
| AwsSolutions-S2 | S3 Bucket 应阻止公开访问 | 添加 `blockPublicAccess` |
| AwsSolutions-IAM4 | 不应使用 AWS 托管策略 | 使用 Grant 方法 |
| AwsSolutions-IAM5 | IAM 策略不应使用通配符 | 限制 resources |
| AwsSolutions-RDS10 | RDS 应启用删除保护 | 添加 `deletionProtection: true` |
| AwsSolutions-ELB2 | ALB 应启用访问日志 | 添加 `accessLogsBucket` |

---

## 6. 审计和监控

### 6.1 CloudTrail

```typescript
const trail = new cloudtrail.Trail(this, 'AuditTrail', {
  bucket: logBucket,
  isMultiRegionTrail: true,
  includeGlobalServiceEvents: true,
  enableFileValidation: true,
});
```

### 6.2 Config Rules

```typescript
new config.ManagedRule(this, 'S3PublicReadProhibited', {
  identifier: config.ManagedRuleIdentifiers.S3_BUCKET_PUBLIC_READ_PROHIBITED,
});

new config.ManagedRule(this, 'RdsEncrypted', {
  identifier: config.ManagedRuleIdentifiers.RDS_STORAGE_ENCRYPTED,
});
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [construct-design.md](construct-design.md) | 安全默认配置 |
| [testing.md](testing.md) | CDK Nag 测试 |
| [AWS Well-Architected - Security](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/) | 外部参考 |

# 安全规范 (Security Standards)

> **职责**: 定义 IAM 最小权限、密钥管理、网络安全、数据加密和 CDK Nag 合规规范。

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
// ✅ Grant 方法自动创建最小权限策略
bucket.grantRead(lambdaFn);
bucket.grantWrite(lambdaFn);

// ❌ 禁止 - 过宽策略
lambdaFn.addToRolePolicy(new iam.PolicyStatement({
  actions: ['s3:*'],
  resources: ['*'],
}));
```

### 1.2 精细权限控制

```typescript
// ✅ 限制资源范围和条件
bucket.grantRead(lambdaFn, 'data/*');  // 仅限 data/ 前缀

const policy = new iam.PolicyStatement({
  actions: ['s3:GetObject'],
  resources: [bucket.arnForObjects('reports/*')],
  conditions: { StringEquals: { 's3:ExistingObjectTag/Environment': 'prod' } },
});
```

### 1.3 避免 Admin 权限

```typescript
// ❌ 禁止 - 管理员权限
managedPolicies: [iam.ManagedPolicy.fromAwsManagedPolicyName('AdministratorAccess')]

// ✅ 正确 - 最小权限
bucket.grantRead(role);
table.grantReadWriteData(role);
```

---

## 2. 密钥管理

### 2.1 Secrets Manager

```typescript
// ✅ 敏感凭证使用 Secrets Manager
const dbSecret = new secretsmanager.Secret(this, 'DbSecret', {
  secretName: 'prod/db/credentials',
  generateSecretString: {
    secretStringTemplate: JSON.stringify({ username: 'admin' }),
    generateStringKey: 'password',
    passwordLength: 32,
  },
});

// RDS 使用: rds.Credentials.fromSecret(dbSecret)
// Lambda 使用: dbSecret.grantRead(fn)
```

### 2.2 SSM Parameter Store

```typescript
// 非敏感配置: SSM Parameter | 敏感配置: Secrets Manager
new ssm.StringParameter(this, 'Config', {
  parameterName: '/app/config/api-url',
  stringValue: 'https://api.example.com',
});
```

### 2.3 禁止硬编码

```typescript
// ❌ 禁止
environment: { API_KEY: 'sk-1234567890abcdef' }

// ✅ 从 Secrets Manager 读取
const secret = secretsmanager.Secret.fromSecretNameV2(this, 'ApiKey', 'prod/api-key');
environment: { API_KEY_SECRET_ARN: secret.secretArn }
secret.grantRead(fn);
```

---

## 3. 网络安全

### 3.1 VPC 分层子网

| 子网类型 | 用途 | 示例资源 |
|---------|------|---------|
| `PUBLIC` | 公网入口 | ALB, NAT Gateway |
| `PRIVATE_WITH_EGRESS` | 应用层 | ECS, Lambda |
| `PRIVATE_ISOLATED` | 数据层 | RDS, ElastiCache |

**关键规则**:
- ✅ 数据库必须放 `PRIVATE_ISOLATED`
- ❌ 禁止 RDS 在 `PUBLIC` 子网

```typescript
// 数据库放在隔离子网
const database = new rds.DatabaseCluster(this, 'Database', {
  vpc,
  vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
});
```

### 3.2 Security Groups

```typescript
// ✅ 最小开放端口 + 禁止所有出站
const dbSecurityGroup = new ec2.SecurityGroup(this, 'DbSg', {
  vpc,
  allowAllOutbound: false,
});
dbSecurityGroup.addIngressRule(appSecurityGroup, ec2.Port.tcp(3306), 'Allow MySQL from app');
```

### 3.3 VPC Endpoints

```typescript
// 减少流量外泄风险
vpc.addInterfaceEndpoint('SecretsManager', { service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER });
vpc.addGatewayEndpoint('S3', { service: ec2.GatewayVpcEndpointAwsService.S3 });
```

---

## 4. 数据加密

### 4.1 S3 加密

- ✅ `encryption: S3_MANAGED` 或 `KMS`
- ✅ `enforceSSL: true` + `blockPublicAccess: BLOCK_ALL`
- 🔐 敏感数据: CMK + `enableKeyRotation: true`

> 代码模板见 [construct-design.md §3](construct-design.md#3-安全默认配置)

### 4.2 RDS 加密

- ✅ `storageEncrypted: true`
- 🔐 敏感数据使用自定义 KMS 密钥

> 代码模板见 [construct-design.md §3](construct-design.md#3-安全默认配置)

### 4.3 传输加密

```typescript
// ALB: HTTPS + TLS 1.2 + HTTP→HTTPS 重定向
lb.addListener('Https', { port: 443, certificates: [cert], sslPolicy: elbv2.SslPolicy.TLS12 });
lb.addListener('Http', { port: 80, defaultAction: elbv2.ListenerAction.redirect({ protocol: 'HTTPS', port: '443', permanent: true }) });
```

---

## 5. CDK Nag

### 5.1 启用 CDK Nag

```typescript
// bin/app.ts
import { Aspects } from 'aws-cdk-lib';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';

Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
```

### 5.2 抑制规则

> **粒度原则**: 优先 `addResourceSuppressions` (精确到资源) → 仅在确实需要时使用 `addStackSuppressions` (Stack 级)。Stack 级抑制可能导致后续新增资源被意外跳过检查。

```typescript
// ✅ 首选 - 资源级抑制 (精确、安全)
NagSuppressions.addResourceSuppressions(bucket, [
  { id: 'AwsSolutions-S1', reason: '此 Bucket 用于 CloudTrail 日志，不需要访问日志' },
]);

// ⚠️ 慎用 - Stack 级抑制 (影响范围大，需额外说明)
NagSuppressions.addStackSuppressions(stack, [
  { id: 'AwsSolutions-IAM4', reason: '使用 AWS 托管策略是此用例的最佳实践' },
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

## 6. 审计监控

```typescript
// CloudTrail + Config Rules
const trail = new cloudtrail.Trail(this, 'Trail', {
  bucket: logBucket,
  isMultiRegionTrail: true,
  enableFileValidation: true,
});

new config.ManagedRule(this, 'S3Public', {
  identifier: config.ManagedRuleIdentifiers.S3_BUCKET_PUBLIC_READ_PROHIBITED,
});
new config.ManagedRule(this, 'RdsEncrypt', {
  identifier: config.ManagedRuleIdentifiers.RDS_STORAGE_ENCRYPTED,
});
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [construct-design.md](construct-design.md) | 安全默认配置代码模板 |
| [testing.md](testing.md) | CDK Nag 测试 |
| [AWS Well-Architected - Security](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/) | 外部参考 |

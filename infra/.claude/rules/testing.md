# 测试规范 (Testing Standards)

> TDD 工作流见 CLAUDE.md

---

## 0. 速查卡片

### 命令

```bash
pnpm test                         # 运行所有测试
pnpm test:coverage                # 测试 + 覆盖率
pnpm test:watch                   # 监听模式
pnpm test lib/constructs/vpc/     # 指定目录
```

### 测试类型

| 类型 | 用途 | 工具 |
|------|------|------|
| **Fine-grained** | 验证特定资源属性 | CDK Assertions |
| **Snapshot** | 检测意外变更 | Jest Snapshot |
| **Compliance** | 安全合规检查 | CDK Nag |

### CDK Assertions 速查

```typescript
// 资源存在
template.hasResourceProperties('AWS::S3::Bucket', { ... });

// 资源计数
template.resourceCountIs('AWS::Lambda::Function', 2);

// 输出存在
template.hasOutput('VpcId', { ... });

// 映射存在
template.hasMapping('RegionMap', { ... });

// 匹配器
Match.objectLike({ ... })    // 部分匹配
Match.exact({ ... })         // 精确匹配
Match.anyValue()             // 任意值
Match.absent()               // 不存在
```

### PR Review 检查清单

- [ ] 每个 Construct 有对应测试
- [ ] 关键属性有 Fine-grained 断言
- [ ] 有 Snapshot 测试检测意外变更
- [ ] CDK Nag 检查通过

---

## 1. 测试文件位置

### Construct 测试 (与源码同目录)

```
lib/constructs/
├── vpc/
│   ├── index.ts
│   ├── vpc.construct.ts
│   └── vpc.construct.test.ts   # 单元测试
├── aurora/
│   ├── index.ts
│   ├── aurora.construct.ts
│   └── aurora.construct.test.ts
```

### 集成测试 (test 目录)

```
test/
├── stacks/
│   ├── network-stack.test.ts
│   └── compute-stack.test.ts
├── snapshot/
│   └── main.test.ts            # 快照测试
└── compliance/
    └── cdk-nag.test.ts         # CDK Nag 测试
```

---

## 2. Fine-grained Assertions

### 2.1 基本模板

```typescript
// lib/constructs/vpc/vpc.construct.test.ts
import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { VpcConstruct } from './vpc.construct';

describe('VpcConstruct', () => {
  let app: cdk.App;
  let stack: cdk.Stack;
  let template: Template;

  beforeEach(() => {
    app = new cdk.App();
    stack = new cdk.Stack(app, 'TestStack');
  });

  it('should create VPC with correct CIDR', () => {
    new VpcConstruct(stack, 'TestVpc', {
      vpcCidr: '10.0.0.0/16',
    });

    template = Template.fromStack(stack);

    template.hasResourceProperties('AWS::EC2::VPC', {
      CidrBlock: '10.0.0.0/16',
      EnableDnsHostnames: true,
      EnableDnsSupport: true,
    });
  });

  it('should create NAT Gateway when enabled', () => {
    new VpcConstruct(stack, 'TestVpc', {
      vpcCidr: '10.0.0.0/16',
      enableNatGateway: true,
      maxAzs: 2,
    });

    template = Template.fromStack(stack);

    template.resourceCountIs('AWS::EC2::NatGateway', 2);
  });

  it('should not create NAT Gateway when disabled', () => {
    new VpcConstruct(stack, 'TestVpc', {
      vpcCidr: '10.0.0.0/16',
      enableNatGateway: false,
    });

    template = Template.fromStack(stack);

    template.resourceCountIs('AWS::EC2::NatGateway', 0);
  });
});
```

### 2.2 Match 对象

```typescript
describe('AuroraConstruct', () => {
  it('should create cluster with security defaults', () => {
    new AuroraConstruct(stack, 'TestAurora', {
      vpc,
    });

    template = Template.fromStack(stack);

    template.hasResourceProperties('AWS::RDS::DBCluster', {
      StorageEncrypted: true,
      DeletionProtection: true,
      // 部分匹配
      BackupRetentionPeriod: Match.anyValue(),
    });
  });

  it('should have correct IAM authentication', () => {
    template.hasResourceProperties('AWS::RDS::DBCluster', {
      EnableIAMDatabaseAuthentication: true,
      // 确保不存在某些属性
      PubliclyAccessible: Match.absent(),
    });
  });
});
```

### 2.3 验证 IAM 策略

```typescript
describe('Lambda with S3 access', () => {
  it('should have S3 read permissions', () => {
    template.hasResourceProperties('AWS::IAM::Policy', {
      PolicyDocument: {
        Statement: Match.arrayWith([
          Match.objectLike({
            Action: Match.arrayWith(['s3:GetObject*', 's3:GetBucket*']),
            Effect: 'Allow',
          }),
        ]),
      },
    });
  });
});
```

---

## 3. Snapshot 测试

### 3.1 基本用法

```typescript
// test/snapshot/main.test.ts
import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { NetworkStack } from '../../lib/stacks/network-stack';

describe('Snapshot Tests', () => {
  it('NetworkStack matches snapshot', () => {
    const app = new cdk.App();
    const stack = new NetworkStack(app, 'TestNetworkStack', {
      env: { account: '123456789012', region: 'ap-northeast-1' },
      vpcCidr: '10.0.0.0/16',
    });

    const template = Template.fromStack(stack);

    // 快照匹配
    expect(template.toJSON()).toMatchSnapshot();
  });
});
```

### 3.2 更新快照

```bash
# 更新所有快照
pnpm test -- -u

# 更新特定快照
pnpm test test/snapshot/main.test.ts -- -u
```

---

## 4. CDK Nag 测试

### 4.1 基本配置

```typescript
// test/compliance/cdk-nag.test.ts
import * as cdk from 'aws-cdk-lib';
import { Aspects } from 'aws-cdk-lib';
import { AwsSolutionsChecks } from 'cdk-nag';
import { NetworkStack } from '../../lib/stacks/network-stack';

describe('CDK Nag Compliance', () => {
  let app: cdk.App;
  let stack: cdk.Stack;

  beforeEach(() => {
    app = new cdk.App();
    stack = new NetworkStack(app, 'TestStack', {
      env: { account: '123456789012', region: 'ap-northeast-1' },
      vpcCidr: '10.0.0.0/16',
    });
  });

  it('should pass AWS Solutions checks', () => {
    Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    const messages = app.synth().getStackArtifact(stack.artifactId).messages;
    const errors = messages.filter((m) => m.level === 'error');

    expect(errors).toHaveLength(0);
  });
});
```

### 4.2 检查特定规则

```typescript
it('should not have S3 buckets without encryption', () => {
  Aspects.of(stack).add(new AwsSolutionsChecks());

  const messages = app.synth().getStackArtifact(stack.artifactId).messages;
  const s3Errors = messages.filter(
    (m) => m.level === 'error' && m.entry.data?.includes('AwsSolutions-S3')
  );

  expect(s3Errors).toHaveLength(0);
});
```

---

## 5. Jest 配置

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'node',
  roots: ['<rootDir>/lib', '<rootDir>/test'],
  testMatch: ['**/*.test.ts'],
  transform: {
    '^.+\\.tsx?$': 'ts-jest',
  },
  collectCoverageFrom: [
    'lib/**/*.ts',
    '!lib/**/*.d.ts',
    '!lib/**/*.test.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 85,
      statements: 85,
    },
  },
};
```

---

## 6. 覆盖率要求

| 层级 | 最低覆盖率 | 目标覆盖率 |
|------|-----------|-----------|
| Constructs | 90% | 95% |
| Stacks | 85% | 90% |
| **整体** | **85%** | **90%** |

---

## 7. 测试最佳实践

### 7.1 测试什么

```typescript
// ✅ 测试业务逻辑和配置
it('should create VPC with 3 AZs by default', () => { ... });
it('should enable encryption on S3 bucket', () => { ... });
it('should grant Lambda read access to S3', () => { ... });

// ❌ 不要测试 CDK 内部实现
it('should create VPC in correct order', () => { ... }); // 不需要
```

### 7.2 隔离测试

```typescript
// 每个测试独立创建 stack
beforeEach(() => {
  app = new cdk.App();
  stack = new cdk.Stack(app, 'TestStack');
});

// 不要共享状态
// ❌ let stack = new cdk.Stack(...);  // 全局共享
```

### 7.3 有意义的断言

```typescript
// ✅ 验证关键安全属性
template.hasResourceProperties('AWS::S3::Bucket', {
  PublicAccessBlockConfiguration: {
    BlockPublicAcls: true,
    BlockPublicPolicy: true,
    IgnorePublicAcls: true,
    RestrictPublicBuckets: true,
  },
});

// ❌ 不要只验证资源存在
template.resourceCountIs('AWS::S3::Bucket', 1); // 不够
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [construct-design.md](construct-design.md) | Construct 设计模式 |
| [security.md](security.md) | 安全配置测试 |
| [CLAUDE.md](../CLAUDE.md) | TDD 工作流 |

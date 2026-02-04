# 部署规范 (Deployment Standards)

> Claude 执行部署相关操作时优先查阅此文档

---

## 0. 速查卡片

### 部署命令

```bash
# 合成模板
pnpm cdk synth

# 查看变更
pnpm cdk diff

# 部署单个 Stack
pnpm cdk deploy NetworkStack-dev

# 部署所有 Stack
pnpm cdk deploy --all

# 指定环境部署
pnpm cdk deploy --context env=prod --all

# 销毁 Stack
pnpm cdk destroy NetworkStack-dev
```

### 环境矩阵

| 环境 | 用途 | 部署方式 | 审批 |
|------|------|---------|------|
| dev | 开发测试 | 手动 | 无 |
| staging | 预发布 | CI/CD | 自动 |
| prod | 生产 | CI/CD | 手动审批 |

### 部署检查清单

- [ ] `cdk diff` 确认变更
- [ ] 测试通过
- [ ] CDK Nag 检查通过
- [ ] 环境变量配置正确
- [ ] 有回滚计划

### PR Review 检查清单

- [ ] 环境配置使用 CDK Context
- [ ] 敏感信息不在代码中
- [ ] 有适当的 RemovalPolicy
- [ ] CI/CD Pipeline 配置正确

---

## 1. 环境配置

### 1.1 CDK Context

```json
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
        "maxCapacity": 2,
        "removalPolicy": "DESTROY"
      },
      "staging": {
        "account": "123456789013",
        "region": "ap-northeast-1",
        "vpcCidr": "10.1.0.0/16",
        "instanceType": "t3.medium",
        "minCapacity": 2,
        "maxCapacity": 4,
        "removalPolicy": "SNAPSHOT"
      },
      "prod": {
        "account": "123456789014",
        "region": "ap-northeast-1",
        "vpcCidr": "10.2.0.0/16",
        "instanceType": "t3.large",
        "minCapacity": 3,
        "maxCapacity": 10,
        "removalPolicy": "RETAIN"
      }
    }
  }
}
```

### 1.2 环境配置类型

```typescript
// lib/config/environments.ts
import * as cdk from 'aws-cdk-lib';

export interface EnvironmentConfig {
  readonly account: string;
  readonly region: string;
  readonly vpcCidr: string;
  readonly instanceType: string;
  readonly minCapacity: number;
  readonly maxCapacity: number;
  readonly removalPolicy: string;
}

export function getEnvironmentConfig(app: cdk.App, envName: string): EnvironmentConfig {
  const environments = app.node.tryGetContext('environments');
  const config = environments?.[envName];

  if (!config) {
    throw new Error(`未找到环境配置: ${envName}，请检查 cdk.json`);
  }

  return config as EnvironmentConfig;
}

export function getRemovalPolicy(config: EnvironmentConfig): cdk.RemovalPolicy {
  switch (config.removalPolicy) {
    case 'DESTROY':
      return cdk.RemovalPolicy.DESTROY;
    case 'SNAPSHOT':
      return cdk.RemovalPolicy.SNAPSHOT;
    default:
      return cdk.RemovalPolicy.RETAIN;
  }
}
```

### 1.3 使用环境配置

```typescript
// bin/app.ts
#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { getEnvironmentConfig, getRemovalPolicy } from '../lib/config/environments';
import { NetworkStack } from '../lib/stacks/network-stack';
import { ComputeStack } from '../lib/stacks/compute-stack';

const app = new cdk.App();
const envName = app.node.tryGetContext('env') || 'dev';
const envConfig = getEnvironmentConfig(app, envName);

const networkStack = new NetworkStack(app, `NetworkStack-${envName}`, {
  env: { account: envConfig.account, region: envConfig.region },
  vpcCidr: envConfig.vpcCidr,
  removalPolicy: getRemovalPolicy(envConfig),
});

const computeStack = new ComputeStack(app, `ComputeStack-${envName}`, {
  env: { account: envConfig.account, region: envConfig.region },
  vpc: networkStack.vpc,
  instanceType: envConfig.instanceType,
  minCapacity: envConfig.minCapacity,
  maxCapacity: envConfig.maxCapacity,
});

// 添加环境标签
cdk.Tags.of(app).add('Environment', envName);
cdk.Tags.of(app).add('Project', 'ai-agents-platform');
cdk.Tags.of(app).add('ManagedBy', 'cdk');

app.synth();
```

---

## 2. CI/CD Pipeline

### 2.1 GitHub Actions

```yaml
# .github/workflows/cdk-deploy.yml
name: CDK Deploy

on:
  push:
    branches:
      - main
    paths:
      - 'infra/**'
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - staging
          - prod

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v2
        with:
          version: 8

      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'pnpm'
          cache-dependency-path: 'infra/pnpm-lock.yaml'

      - name: Install dependencies
        working-directory: infra
        run: pnpm install

      - name: Run tests
        working-directory: infra
        run: pnpm test:coverage

      - name: CDK Synth
        working-directory: infra
        run: pnpm cdk synth --context env=${{ github.event.inputs.environment || 'dev' }}

  deploy-dev:
    needs: test
    if: github.ref == 'refs/heads/main' && (github.event.inputs.environment == 'dev' || github.event_name == 'push')
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1

      - uses: pnpm/action-setup@v2
        with:
          version: 8

      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'pnpm'
          cache-dependency-path: 'infra/pnpm-lock.yaml'

      - name: Install dependencies
        working-directory: infra
        run: pnpm install

      - name: CDK Deploy
        working-directory: infra
        run: pnpm cdk deploy --all --context env=dev --require-approval never

  deploy-staging:
    needs: deploy-dev
    if: github.event.inputs.environment == 'staging'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      # 类似 dev 的步骤...

  deploy-prod:
    needs: deploy-staging
    if: github.event.inputs.environment == 'prod'
    runs-on: ubuntu-latest
    environment:
      name: prod
      # 生产环境需要手动审批
    steps:
      # 类似 dev 的步骤...
```

### 2.2 CDK Pipeline (AWS 原生)

```typescript
// lib/stacks/pipeline-stack.ts
import * as cdk from 'aws-cdk-lib';
import { CodePipeline, CodePipelineSource, ShellStep } from 'aws-cdk-lib/pipelines';
import { Construct } from 'constructs';

export class PipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const pipeline = new CodePipeline(this, 'Pipeline', {
      pipelineName: 'AiAgentsPlatform',
      synth: new ShellStep('Synth', {
        input: CodePipelineSource.gitHub('owner/repo', 'main', {
          authentication: cdk.SecretValue.secretsManager('github-token'),
        }),
        commands: [
          'cd infra',
          'pnpm install',
          'pnpm test',
          'pnpm cdk synth',
        ],
        primaryOutputDirectory: 'infra/cdk.out',
      }),
    });

    // Dev 阶段
    pipeline.addStage(new DeployStage(this, 'Dev', {
      env: { account: '123456789012', region: 'ap-northeast-1' },
      envName: 'dev',
    }));

    // Staging 阶段
    pipeline.addStage(new DeployStage(this, 'Staging', {
      env: { account: '123456789013', region: 'ap-northeast-1' },
      envName: 'staging',
    }));

    // Prod 阶段 (需要手动审批)
    pipeline.addStage(new DeployStage(this, 'Prod', {
      env: { account: '123456789014', region: 'ap-northeast-1' },
      envName: 'prod',
    }), {
      pre: [
        new pipelines.ManualApprovalStep('Approve'),
      ],
    });
  }
}
```

---

## 3. 部署流程

### 3.1 手动部署流程

```bash
# 1. 确认当前环境
echo $AWS_PROFILE

# 2. 合成并检查变更
pnpm cdk synth --context env=dev
pnpm cdk diff --context env=dev

# 3. 运行测试
pnpm test

# 4. 部署
pnpm cdk deploy --all --context env=dev

# 5. 验证部署
aws cloudformation describe-stacks --stack-name NetworkStack-dev
```

### 3.2 部署顺序

```
1. NetworkStack (基础网络)
     ↓
2. SecurityStack (安全组、IAM)
     ↓
3. DatabaseStack (数据库)
     ↓
4. ComputeStack (计算资源)
     ↓
5. ApiStack (API 层)
     ↓
6. MonitoringStack (监控)
```

### 3.3 回滚策略

```bash
# 回滚到上一个版本
pnpm cdk deploy --all --context env=dev --rollback

# 或使用 CloudFormation 控制台回滚

# 紧急情况：销毁并重建
pnpm cdk destroy ComputeStack-dev
pnpm cdk deploy ComputeStack-dev --context env=dev
```

---

## 4. 蓝绿部署

### 4.1 ECS 蓝绿部署

```typescript
// 使用 CodeDeploy 进行蓝绿部署
import * as codedeploy from 'aws-cdk-lib/aws-codedeploy';

const deployment = new codedeploy.EcsDeploymentGroup(this, 'DeploymentGroup', {
  service: ecsService,
  blueGreenDeploymentConfig: {
    blueTargetGroup: blueTargetGroup,
    greenTargetGroup: greenTargetGroup,
    listener: listener,
    testListener: testListener,
  },
  deploymentConfig: codedeploy.EcsDeploymentConfig.LINEAR_10PERCENT_EVERY_1MINUTES,
  autoRollback: {
    failedDeployment: true,
    stoppedDeployment: true,
  },
});
```

---

## 5. 安全部署

### 5.1 部署前检查

```bash
# 检查 CDK Nag
pnpm test test/compliance/

# 检查敏感信息
git secrets --scan

# 检查依赖漏洞
pnpm audit
```

### 5.2 部署权限

```typescript
// 部署 Role 最小权限
const deployRole = new iam.Role(this, 'DeployRole', {
  assumedBy: new iam.ServicePrincipal('codebuild.amazonaws.com'),
  managedPolicies: [
    // 仅授予必要的 CloudFormation 权限
    iam.ManagedPolicy.fromAwsManagedPolicyName('AWSCloudFormationFullAccess'),
  ],
});

// 添加特定资源权限
deployRole.addToPolicy(new iam.PolicyStatement({
  actions: ['sts:AssumeRole'],
  resources: ['arn:aws:iam::*:role/cdk-*'],
}));
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [architecture.md](architecture.md) | Stack 依赖关系 |
| [security.md](security.md) | 部署安全 |
| [cost-optimization.md](cost-optimization.md) | 环境成本管理 |

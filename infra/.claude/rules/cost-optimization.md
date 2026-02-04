# 成本优化规范 (Cost Optimization Standards)

> Claude 设计基础设施时优先查阅此文档

基于 AWS Well-Architected Framework 成本优化支柱的 CDK 成本管理规范。

---

## 0. 速查卡片

### 成本优化决策矩阵

| 资源类型 | Dev 环境 | Staging 环境 | Prod 环境 |
|---------|---------|-------------|---------|
| EC2/ECS | t3.small, 按需 | t3.medium, 按需 | t3.large, Reserved/Savings |
| RDS | db.t3.small, 单 AZ | db.t3.medium, 多 AZ | db.r6g.large, 多 AZ, Reserved |
| NAT Gateway | 1 个 | 2 个 | 3 个 (每 AZ) |
| S3 | Intelligent-Tiering | Intelligent-Tiering | Intelligent-Tiering + 生命周期 |
| Lambda | 默认 | 默认 | 优化内存配置 |

### 成本标签 (必须)

```typescript
Tags.of(app).add('Project', 'ai-agents-platform');
Tags.of(app).add('Environment', envName);
Tags.of(app).add('CostCenter', 'ai-platform');
Tags.of(app).add('ManagedBy', 'cdk');
```

### PR Review 检查清单

- [ ] 所有资源有成本标签
- [ ] Dev 环境使用最小规格
- [ ] 有资源清理策略 (RemovalPolicy)
- [ ] S3 有生命周期规则
- [ ] 考虑 Reserved/Savings Plans (Prod)

---

## 1. 实例选型

### 1.1 环境差异化配置

```typescript
// lib/config/environments.ts
export const instanceConfigs = {
  dev: {
    ec2: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.SMALL),
    rds: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.SMALL),
    elasticache: 'cache.t3.micro',
    natGateways: 1,
  },
  staging: {
    ec2: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM),
    rds: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM),
    elasticache: 'cache.t3.small',
    natGateways: 2,
  },
  prod: {
    ec2: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.LARGE),
    rds: ec2.InstanceType.of(ec2.InstanceClass.R6G, ec2.InstanceSize.LARGE),
    elasticache: 'cache.r6g.large',
    natGateways: 3,
  },
};
```

### 1.2 自动扩缩

```typescript
// ECS 自动扩缩
const scaling = service.autoScaleTaskCount({
  minCapacity: envConfig.minCapacity,
  maxCapacity: envConfig.maxCapacity,
});

scaling.scaleOnCpuUtilization('CpuScaling', {
  targetUtilizationPercent: 70,
  scaleInCooldown: cdk.Duration.seconds(60),
  scaleOutCooldown: cdk.Duration.seconds(60),
});

// 定时扩缩 (非工作时间缩减)
if (envName === 'dev') {
  scaling.scaleOnSchedule('ScaleDown', {
    schedule: appscaling.Schedule.cron({ hour: '20', minute: '0' }), // 20:00
    minCapacity: 0,
    maxCapacity: 0,
  });

  scaling.scaleOnSchedule('ScaleUp', {
    schedule: appscaling.Schedule.cron({ hour: '8', minute: '0' }), // 08:00
    minCapacity: 1,
    maxCapacity: 2,
  });
}
```

---

## 2. 存储优化

### 2.1 S3 生命周期

```typescript
const bucket = new s3.Bucket(this, 'DataBucket', {
  // 智能分层
  intelligentTieringConfigurations: [
    {
      name: 'DefaultTiering',
      archiveAccessTierTime: cdk.Duration.days(90),
      deepArchiveAccessTierTime: cdk.Duration.days(180),
    },
  ],

  // 生命周期规则
  lifecycleRules: [
    {
      id: 'TransitionToIA',
      transitions: [
        {
          storageClass: s3.StorageClass.INFREQUENT_ACCESS,
          transitionAfter: cdk.Duration.days(30),
        },
        {
          storageClass: s3.StorageClass.GLACIER,
          transitionAfter: cdk.Duration.days(90),
        },
      ],
    },
    {
      id: 'ExpireOldVersions',
      noncurrentVersionExpiration: cdk.Duration.days(30),
    },
    {
      id: 'AbortMultipartUpload',
      abortIncompleteMultipartUploadAfter: cdk.Duration.days(7),
    },
  ],
});
```

### 2.2 EBS 优化

```typescript
// 使用 gp3 而非 gp2
const volume = new ec2.Volume(this, 'DataVolume', {
  volumeType: ec2.EbsDeviceVolumeType.GP3,
  size: cdk.Size.gibibytes(100),
  iops: 3000, // gp3 可自定义 IOPS
  throughput: 125,
});
```

---

## 3. 网络优化

### 3.1 NAT Gateway 优化

```typescript
// Dev: 单 NAT Gateway
// Prod: 每 AZ 一个 NAT Gateway (高可用)
const vpc = new ec2.Vpc(this, 'Vpc', {
  maxAzs: 3,
  natGateways: envConfig.natGateways,
  natGatewaySubnets: {
    subnetType: ec2.SubnetType.PUBLIC,
    onePerAz: envName === 'prod',
  },
});

// 考虑 NAT Instance 替代 (Dev 环境)
if (envName === 'dev') {
  // 使用 NAT Instance 节省成本
  // NAT Gateway: ~$30/月
  // NAT Instance (t3.nano): ~$4/月
}
```

### 3.2 VPC Endpoints

```typescript
// 使用 VPC Endpoints 减少 NAT 流量费用
vpc.addGatewayEndpoint('S3Endpoint', {
  service: ec2.GatewayVpcEndpointAwsService.S3,
});

vpc.addGatewayEndpoint('DynamoDBEndpoint', {
  service: ec2.GatewayVpcEndpointAwsService.DYNAMODB,
});

// Interface Endpoints (按需添加)
if (envName === 'prod') {
  vpc.addInterfaceEndpoint('SecretsManagerEndpoint', {
    service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
  });
}
```

---

## 4. 计算优化

### 4.1 Lambda 内存优化

```typescript
// 使用 AWS Lambda Power Tuning 确定最优配置
const fn = new lambda.Function(this, 'Handler', {
  // 根据实际测试结果设置
  memorySize: envConfig.lambdaMemory ?? 256,
  timeout: cdk.Duration.seconds(30),

  // 使用 ARM 架构节省成本 (约 20%)
  architecture: lambda.Architecture.ARM_64,
});
```

### 4.2 Spot 实例

```typescript
// ECS Spot 实例 (非关键工作负载)
const spotCapacityProvider = new ecs.AsgCapacityProvider(this, 'SpotCapacity', {
  autoScalingGroup: new autoscaling.AutoScalingGroup(this, 'SpotAsg', {
    vpc,
    instanceType: envConfig.ec2,
    machineImage: ecs.EcsOptimizedImage.amazonLinux2(),
    spotPrice: '0.05', // 设置最高价格
  }),
});

cluster.addAsgCapacityProvider(spotCapacityProvider);
```

---

## 5. 成本标签

### 5.1 标签策略

```typescript
// bin/app.ts
import * as cdk from 'aws-cdk-lib';

const app = new cdk.App();
const envName = app.node.tryGetContext('env') || 'dev';

// 必须标签
const requiredTags: Record<string, string> = {
  Project: 'ai-agents-platform',
  Environment: envName,
  ManagedBy: 'cdk',
  CostCenter: 'ai-platform',
  Owner: 'platform-team',
};

// 应用到所有资源
Object.entries(requiredTags).forEach(([key, value]) => {
  cdk.Tags.of(app).add(key, value);
});

// 环境特定标签
if (envName === 'prod') {
  cdk.Tags.of(app).add('Criticality', 'high');
  cdk.Tags.of(app).add('DataClassification', 'confidential');
}
```

### 5.2 成本分配标签

在 AWS Billing Console 中启用成本分配标签：
- `Project`
- `Environment`
- `CostCenter`

---

## 6. 资源清理

### 6.1 RemovalPolicy

```typescript
// Dev: 允许销毁
const devBucket = new s3.Bucket(this, 'DevBucket', {
  removalPolicy: cdk.RemovalPolicy.DESTROY,
  autoDeleteObjects: true,
});

// Prod: 保留
const prodBucket = new s3.Bucket(this, 'ProdBucket', {
  removalPolicy: cdk.RemovalPolicy.RETAIN,
});

// 数据库: 快照
const database = new rds.DatabaseCluster(this, 'Database', {
  removalPolicy: envName === 'prod'
    ? cdk.RemovalPolicy.SNAPSHOT
    : cdk.RemovalPolicy.DESTROY,
});
```

### 6.2 定期清理

```typescript
// CloudWatch Logs 保留期限
new logs.LogGroup(this, 'AppLogs', {
  retention: envName === 'prod'
    ? logs.RetentionDays.ONE_YEAR
    : logs.RetentionDays.ONE_WEEK,
  removalPolicy: cdk.RemovalPolicy.DESTROY,
});
```

---

## 7. 成本监控

### 7.1 预算告警

```typescript
import * as budgets from 'aws-cdk-lib/aws-budgets';

new budgets.CfnBudget(this, 'MonthlyBudget', {
  budget: {
    budgetName: `ai-platform-${envName}-monthly`,
    budgetLimit: {
      amount: envName === 'prod' ? 1000 : 100,
      unit: 'USD',
    },
    budgetType: 'COST',
    timeUnit: 'MONTHLY',
  },
  notificationsWithSubscribers: [
    {
      notification: {
        comparisonOperator: 'GREATER_THAN',
        notificationType: 'ACTUAL',
        threshold: 80,
        thresholdType: 'PERCENTAGE',
      },
      subscribers: [
        {
          address: 'platform-team@example.com',
          subscriptionType: 'EMAIL',
        },
      ],
    },
  ],
});
```

### 7.2 Cost Explorer 标签

确保在 Cost Explorer 中启用按标签分组：
1. AWS Console → Billing → Cost Explorer
2. 启用 `Project`, `Environment`, `CostCenter` 标签

---

## 8. 成本审计清单

### 月度审计

- [ ] 检查未使用的 EBS 卷
- [ ] 检查未关联的弹性 IP
- [ ] 检查空闲的负载均衡器
- [ ] 审查 Reserved Instances 利用率
- [ ] 检查 S3 存储类使用情况

### 季度审计

- [ ] 评估 Reserved Instances / Savings Plans 续期
- [ ] 审查实例类型是否合适
- [ ] 评估是否可以使用 Spot 实例
- [ ] 检查跨区域数据传输

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [deployment.md](deployment.md) | 环境配置 |
| [architecture.md](architecture.md) | 资源设计 |
| [AWS Well-Architected - Cost](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/) | 外部参考 |

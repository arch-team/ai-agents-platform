#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { AwsSolutionsChecks } from 'cdk-nag';
import { getEnvironmentConfig, getRequiredTags, isDev, isProd } from '../lib/config';
import {
  NetworkStack,
  SecurityStack,
  DatabaseStack,
  ComputeStack,
  AgentCoreStack,
  MonitoringStack,
  FrontendStack,
  BillingStack,
} from '../lib/stacks';

const app = new cdk.App();
const envConfig = getEnvironmentConfig(app);

// 应用必须标签
for (const [key, value] of Object.entries(getRequiredTags(envConfig.envName))) {
  cdk.Tags.of(app).add(key, value);
}

// 启用 CDK Nag
cdk.Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));

// 提取公共环境配置，避免重复构建 env 对象
const cdkEnv = { account: envConfig.account, region: envConfig.region };
const prefix = `ai-agents-plat`; // Stack 命名前缀
const env = envConfig.envName;

// Stack 实例化 — 命名规范: ai-agents-plat-{stack}-{env}
const networkStack = new NetworkStack(app, `${prefix}-network-${env}`, {
  env: cdkEnv,
  vpcCidr: envConfig.vpcCidr,
  envName: env,
  // Prod: 每 AZ 一个 NAT Gateway (高可用); Dev: 1 个 (默认, 节省成本)
  ...(isProd(env) && { natGateways: 3 }),
});

const securityStack = new SecurityStack(app, `${prefix}-security-${env}`, {
  env: cdkEnv,
  vpc: networkStack.vpc,
  envName: env,
});
securityStack.addDependency(networkStack);

const databaseStack = new DatabaseStack(app, `${prefix}-database-${env}`, {
  env: cdkEnv,
  vpc: networkStack.vpc,
  dbSecurityGroup: securityStack.dbSecurityGroup,
  encryptionKey: securityStack.encryptionKey,
  envName: env,
  // Prod: db.r6g.large (性能优化); Dev: db.t3.medium (默认)
  instanceType: isProd(env)
    ? ec2.InstanceType.of(ec2.InstanceClass.R6G, ec2.InstanceSize.LARGE)
    : undefined,
});
databaseStack.addDependency(networkStack);
databaseStack.addDependency(securityStack);

// AgentCore (ComputeStack 之前创建, 因为 ComputeStack 需要 Runtime ARN)
const agentCoreStack = new AgentCoreStack(app, `${prefix}-agentcore-${env}`, {
  env: cdkEnv,
  vpc: networkStack.vpc,
  envName: env,
});
agentCoreStack.addDependency(networkStack);

// Agent 运行时模式: 从 CDK Context 读取，默认 'agentcore_runtime'
// 用法: cdk deploy --context agentRuntimeMode=in_process (切换到本地 CLI 模式)
const agentRuntimeMode = app.node.tryGetContext('agentRuntimeMode') ?? 'agentcore_runtime';

const computeStack = new ComputeStack(app, `${prefix}-compute-${env}`, {
  env: cdkEnv,
  vpc: networkStack.vpc,
  dbSecurityGroup: securityStack.dbSecurityGroup,
  databaseSecret: databaseStack.dbSecret,
  databaseEndpoint: databaseStack.cluster.clusterEndpoint.hostname,
  // 使用 ARN 字符串避免跨 Stack 循环依赖 (CDK 2.1100+ 行为变化)
  encryptionKeyArn: securityStack.encryptionKey.keyArn,
  jwtSecretArn: securityStack.jwtSecret.secretArn,
  envName: env,
  // Claude Agent SDK bundled CLI 需要充足 CPU/内存运行 Agent Loop
  // Dev: 1024 CPU + 2048 MiB (CLI 子进程 + Python 主进程 + DB 连接)
  // Prod: 1024 CPU + 2048 MiB + 2 任务
  cpu: 1024,
  memoryLimitMiB: 2048,
  ...(isProd(env) && {
    desiredCount: 2,
  }),
  // Agent 运行时模式: 通过 CDK Context 配置化 (默认 agentcore_runtime)
  agentRuntimeMode,
  // AgentCore Runtime ARN (agentcore_runtime 模式: Agent 执行托管在 AgentCore 独立容器中)
  agentcoreRuntimeArn: agentCoreStack.runtimeArn,
  // AgentCore Gateway Cognito 认证参数 (M16: Agent 工具绑定)
  gatewayTokenEndpoint: agentCoreStack.gatewayTokenEndpoint,
  gatewayCognitoClientId: agentCoreStack.gatewayCognitoClientId,
  // Dev: 非工作时段 (UTC 12:00 = 北京 20:00) 缩减到 0，工作时段 (UTC 00:00 = 北京 08:00) 恢复到 1
  ...(isDev(env) && {
    scheduledScaling: {
      scaleDownSchedule: '0 12 * * ? *',
      scaleUpSchedule: '0 0 * * ? *',
      scaleUpMinCapacity: 1,
      scaleUpMaxCapacity: 1,
    },
  }),
});
computeStack.addDependency(networkStack);
computeStack.addDependency(securityStack);
computeStack.addDependency(databaseStack);
computeStack.addDependency(agentCoreStack);

const monitoringStack = new MonitoringStack(app, `${prefix}-monitoring-${env}`, {
  env: cdkEnv,
  cluster: databaseStack.cluster,
  service: computeStack.service,
  loadBalancer: computeStack.loadBalancer,
  targetGroup: computeStack.targetGroup,
  encryptionKey: securityStack.encryptionKey,
  alertEmail: envConfig.alertEmail,
  envName: env,
});
monitoringStack.addDependency(databaseStack);
monitoringStack.addDependency(computeStack);
monitoringStack.addDependency(securityStack);

// FrontendStack — S3 私有 + CloudFront OAC，独立 Stack，无需依赖其他 Stack
new FrontendStack(app, `${prefix}-frontend-${env}`, {
  env: cdkEnv,
  envName: env,
});

// BillingStack — AWS Budgets 月度预算告警，独立 Stack，无需依赖其他 Stack
new BillingStack(app, `${prefix}-billing-${env}`, {
  env: cdkEnv,
  envName: env,
  alertEmail: envConfig.alertEmail,
});

app.synth();

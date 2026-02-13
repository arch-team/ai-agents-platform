#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Aspects } from 'aws-cdk-lib';
import { AwsSolutionsChecks } from 'cdk-nag';
import { getEnvironmentConfig, getRequiredTags, isDev, isProd } from '../lib/config';
import {
  NetworkStack,
  SecurityStack,
  DatabaseStack,
  ComputeStack,
  AgentCoreStack,
  MonitoringStack,
} from '../lib/stacks';

const app = new cdk.App();
const envConfig = getEnvironmentConfig(app);

// 应用必须标签
const tags = getRequiredTags(envConfig.envName);
Object.entries(tags).forEach(([key, value]) => {
  cdk.Tags.of(app).add(key, value);
});

// 启用 CDK Nag
Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));

// 提取公共环境配置，避免重复构建 env 对象
const cdkEnv = { account: envConfig.account, region: envConfig.region };
const prefix = `ai-agents-plat`;  // Stack 命名前缀
const env = envConfig.envName;

// Stack 实例化 — 命名规范: ai-agents-plat-{stack}-{env}
const networkStack = new NetworkStack(app, `${prefix}-network-${env}`, {
  env: cdkEnv,
  vpcCidr: envConfig.vpcCidr,
  envName: env,
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
  // Prod: 512 CPU / 1024 MiB / 2 任务; Dev: 256 CPU / 512 MiB / 1 任务 (默认)
  ...(isProd(env) && {
    cpu: 512,
    memoryLimitMiB: 1024,
    desiredCount: 2,
  }),
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

const agentCoreStack = new AgentCoreStack(app, `${prefix}-agentcore-${env}`, {
  env: cdkEnv,
  vpc: networkStack.vpc,
  envName: env,
});
agentCoreStack.addDependency(networkStack);

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

app.synth();

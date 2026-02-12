#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { Aspects } from 'aws-cdk-lib';
import { AwsSolutionsChecks } from 'cdk-nag';
import { getEnvironmentConfig, getRequiredTags } from '../lib/config';
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

// Stack 实例化
const networkStack = new NetworkStack(app, `Network-${envConfig.envName}`, {
  env: cdkEnv,
  vpcCidr: envConfig.vpcCidr,
  envName: envConfig.envName,
});

const securityStack = new SecurityStack(app, `Security-${envConfig.envName}`, {
  env: cdkEnv,
  vpc: networkStack.vpc,
  envName: envConfig.envName,
});
securityStack.addDependency(networkStack);

const databaseStack = new DatabaseStack(app, `Database-${envConfig.envName}`, {
  env: cdkEnv,
  vpc: networkStack.vpc,
  dbSecurityGroup: securityStack.dbSecurityGroup,
  encryptionKey: securityStack.encryptionKey,
  envName: envConfig.envName,
});
databaseStack.addDependency(networkStack);
databaseStack.addDependency(securityStack);

const computeStack = new ComputeStack(app, `Compute-${envConfig.envName}`, {
  env: cdkEnv,
  vpc: networkStack.vpc,
  dbSecurityGroup: securityStack.dbSecurityGroup,
  databaseSecret: databaseStack.dbSecret,
  databaseEndpoint: databaseStack.cluster.clusterEndpoint.hostname,
  encryptionKey: securityStack.encryptionKey,
  jwtSecret: securityStack.jwtSecret,
  envName: envConfig.envName,
});
computeStack.addDependency(networkStack);
computeStack.addDependency(securityStack);
computeStack.addDependency(databaseStack);

const agentCoreStack = new AgentCoreStack(app, `AgentCore-${envConfig.envName}`, {
  env: cdkEnv,
  vpc: networkStack.vpc,
  envName: envConfig.envName,
});
agentCoreStack.addDependency(networkStack);

const monitoringStack = new MonitoringStack(app, `Monitoring-${envConfig.envName}`, {
  env: cdkEnv,
  cluster: databaseStack.cluster,
  service: computeStack.service,
  loadBalancer: computeStack.loadBalancer,
  targetGroup: computeStack.targetGroup,
  alertEmail: envConfig.alertEmail,
  envName: envConfig.envName,
});
monitoringStack.addDependency(databaseStack);
monitoringStack.addDependency(computeStack);

app.synth();

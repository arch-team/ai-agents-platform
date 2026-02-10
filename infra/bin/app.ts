#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { Aspects } from 'aws-cdk-lib';
import { AwsSolutionsChecks } from 'cdk-nag';
import { getEnvironmentConfig } from '../lib/config/environments';
import { getRequiredTags } from '../lib/config/constants';
import {
  NetworkStack,
  SecurityStack,
  DatabaseStack,
  AgentCoreStack,
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

const agentCoreStack = new AgentCoreStack(
  app,
  `AgentCore-${envConfig.envName}`,
  {
    env: cdkEnv,
    vpc: networkStack.vpc,
    envName: envConfig.envName,
  },
);
agentCoreStack.addDependency(networkStack);

app.synth();

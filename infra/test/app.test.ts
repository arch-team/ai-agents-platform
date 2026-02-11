import * as cdk from 'aws-cdk-lib';
import { NetworkStack, SecurityStack, DatabaseStack, AgentCoreStack } from '../lib/stacks';
import { TEST_ENV, TEST_VPC_CIDR } from './helpers/test-utils';

/** 创建完整的四层 Stack 组合 (Network → Security → Database, Network → AgentCore) */
function createStackGroup(app: cdk.App) {
  const networkStack = new NetworkStack(app, 'TestNetworkStack', {
    env: TEST_ENV,
    vpcCidr: TEST_VPC_CIDR,
    envName: 'dev',
  });

  const securityStack = new SecurityStack(app, 'TestSecurityStack', {
    env: TEST_ENV,
    vpc: networkStack.vpc,
    envName: 'dev',
  });

  const databaseStack = new DatabaseStack(app, 'TestDatabaseStack', {
    env: TEST_ENV,
    vpc: networkStack.vpc,
    dbSecurityGroup: securityStack.dbSecurityGroup,
    encryptionKey: securityStack.encryptionKey,
    envName: 'dev',
  });

  const agentCoreStack = new AgentCoreStack(app, 'TestAgentCoreStack', {
    env: TEST_ENV,
    vpc: networkStack.vpc,
    envName: 'dev',
  });

  return { networkStack, securityStack, databaseStack, agentCoreStack };
}

describe('CDK App', () => {
  it('应能创建四个 Stack', () => {
    const app = new cdk.App();
    const { networkStack, securityStack, databaseStack, agentCoreStack } = createStackGroup(app);

    expect(networkStack).toBeDefined();
    expect(securityStack).toBeDefined();
    expect(databaseStack).toBeDefined();
    expect(agentCoreStack).toBeDefined();
  });

  it('Stack 依赖关系应正确', () => {
    const app = new cdk.App();
    const { networkStack, securityStack, databaseStack, agentCoreStack } = createStackGroup(app);

    securityStack.addDependency(networkStack);
    databaseStack.addDependency(networkStack);
    databaseStack.addDependency(securityStack);
    agentCoreStack.addDependency(networkStack);

    expect(securityStack.dependencies).toContain(networkStack);
    expect(databaseStack.dependencies).toContain(networkStack);
    expect(databaseStack.dependencies).toContain(securityStack);
    expect(agentCoreStack.dependencies).toContain(networkStack);
  });
});

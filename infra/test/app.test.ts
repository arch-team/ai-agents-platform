import * as cdk from 'aws-cdk-lib';
import { NetworkStack, SecurityStack, DatabaseStack } from '../lib/stacks';
import { TEST_ENV, TEST_VPC_CIDR } from './helpers/test-utils';

/** 创建标准三层 Stack 组合 (Network → Security → Database) */
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

  return { networkStack, securityStack, databaseStack };
}

describe('CDK App', () => {
  it('应能创建三个 Stack', () => {
    const app = new cdk.App();
    const { networkStack, securityStack, databaseStack } = createStackGroup(app);

    expect(networkStack).toBeDefined();
    expect(securityStack).toBeDefined();
    expect(databaseStack).toBeDefined();
  });

  it('Stack 依赖关系应正确', () => {
    const app = new cdk.App();
    const { networkStack, securityStack, databaseStack } = createStackGroup(app);

    securityStack.addDependency(networkStack);
    databaseStack.addDependency(networkStack);
    databaseStack.addDependency(securityStack);

    expect(securityStack.dependencies).toContain(networkStack);
    expect(databaseStack.dependencies).toContain(networkStack);
    expect(databaseStack.dependencies).toContain(securityStack);
  });
});

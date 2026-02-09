import * as cdk from 'aws-cdk-lib';
import { NetworkStack, SecurityStack, DatabaseStack } from '../lib/stacks';

describe('CDK App', () => {
  const testEnv = { account: '000000000000', region: 'ap-northeast-1' };

  it('应能创建三个 Stack', () => {
    const app = new cdk.App();

    const networkStack = new NetworkStack(app, 'TestNetworkStack', {
      env: testEnv,
      vpcCidr: '10.0.0.0/16',
      envName: 'dev',
    });

    const securityStack = new SecurityStack(app, 'TestSecurityStack', {
      env: testEnv,
      vpc: networkStack.vpc,
      envName: 'dev',
    });

    const databaseStack = new DatabaseStack(app, 'TestDatabaseStack', {
      env: testEnv,
      vpc: networkStack.vpc,
      dbSecurityGroup: securityStack.dbSecurityGroup,
      encryptionKey: securityStack.encryptionKey,
      envName: 'dev',
    });

    expect(networkStack).toBeDefined();
    expect(securityStack).toBeDefined();
    expect(databaseStack).toBeDefined();
  });

  it('Stack 依赖关系应正确', () => {
    const app = new cdk.App();

    const networkStack = new NetworkStack(app, 'TestNetworkStack', {
      env: testEnv,
      vpcCidr: '10.0.0.0/16',
      envName: 'dev',
    });

    const securityStack = new SecurityStack(app, 'TestSecurityStack', {
      env: testEnv,
      vpc: networkStack.vpc,
      envName: 'dev',
    });
    securityStack.addDependency(networkStack);

    const databaseStack = new DatabaseStack(app, 'TestDatabaseStack', {
      env: testEnv,
      vpc: networkStack.vpc,
      dbSecurityGroup: securityStack.dbSecurityGroup,
      encryptionKey: securityStack.encryptionKey,
      envName: 'dev',
    });
    databaseStack.addDependency(networkStack);
    databaseStack.addDependency(securityStack);

    // 验证依赖关系
    expect(securityStack.dependencies).toContain(networkStack);
    expect(databaseStack.dependencies).toContain(networkStack);
    expect(databaseStack.dependencies).toContain(securityStack);
  });
});

import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import {
  NetworkStack,
  SecurityStack,
  DatabaseStack,
  AgentCoreStack,
} from '../../lib/stacks';
import {
  createCrossStackDbDependencies,
  createVpcDependency,
  TEST_ENV,
  TEST_VPC_CIDR,
} from '../helpers/test-utils';

describe('Snapshot Tests', () => {
  it('NetworkStack 快照匹配', () => {
    const app = new cdk.App();
    const stack = new NetworkStack(app, 'TestNetworkStack', {
      env: TEST_ENV,
      vpcCidr: TEST_VPC_CIDR,
      envName: 'dev',
    });

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });

  it('SecurityStack 快照匹配', () => {
    const app = new cdk.App();
    const vpc = createVpcDependency(app, TEST_ENV);

    const stack = new SecurityStack(app, 'TestSecurityStack', {
      env: TEST_ENV,
      vpc,
      envName: 'dev',
    });

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });

  it('DatabaseStack 快照匹配', () => {
    const app = new cdk.App();
    const { vpc, dbSecurityGroup, encryptionKey } =
      createCrossStackDbDependencies(app, TEST_ENV);

    const stack = new DatabaseStack(app, 'TestDatabaseStack', {
      env: TEST_ENV,
      vpc,
      dbSecurityGroup,
      encryptionKey,
      envName: 'dev',
    });

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });

  it('AgentCoreStack 快照匹配', () => {
    const app = new cdk.App();
    const vpc = createVpcDependency(app, TEST_ENV);

    const stack = new AgentCoreStack(app, 'TestAgentCoreStack', {
      env: TEST_ENV,
      vpc,
      envName: 'dev',
    });

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });
});

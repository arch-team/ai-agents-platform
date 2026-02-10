import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import { Template } from 'aws-cdk-lib/assertions';
import {
  NetworkStack,
  SecurityStack,
  DatabaseStack,
  AgentCoreStack,
} from '../../lib/stacks';
import { createTestVpc, createVpcDependency, TEST_ENV, TEST_VPC_CIDR } from '../helpers/test-utils';

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
    const vpcStack = new cdk.Stack(app, 'VpcStack', { env: TEST_ENV });
    const vpc = createTestVpc(vpcStack);
    const dbSecurityGroup = new ec2.SecurityGroup(vpcStack, 'TestDbSg', {
      vpc,
    });
    const encryptionKey = new kms.Key(vpcStack, 'TestKey');

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

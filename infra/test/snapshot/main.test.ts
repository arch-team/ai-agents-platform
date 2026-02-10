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
import { createTestVpc } from '../helpers/test-utils';

const testEnv = { account: '000000000000', region: 'ap-northeast-1' };

describe('Snapshot Tests', () => {
  it('NetworkStack 快照匹配', () => {
    const app = new cdk.App();
    const stack = new NetworkStack(app, 'TestNetworkStack', {
      env: testEnv,
      vpcCidr: '10.0.0.0/16',
      envName: 'dev',
    });

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });

  it('SecurityStack 快照匹配', () => {
    const app = new cdk.App();
    const vpcStack = new cdk.Stack(app, 'VpcStack', { env: testEnv });
    const vpc = createTestVpc(vpcStack);

    const stack = new SecurityStack(app, 'TestSecurityStack', {
      env: testEnv,
      vpc,
      envName: 'dev',
    });

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });

  it('DatabaseStack 快照匹配', () => {
    const app = new cdk.App();
    const vpcStack = new cdk.Stack(app, 'VpcStack', { env: testEnv });
    const vpc = createTestVpc(vpcStack);
    const dbSecurityGroup = new ec2.SecurityGroup(vpcStack, 'TestDbSg', {
      vpc,
    });
    const encryptionKey = new kms.Key(vpcStack, 'TestKey');

    const stack = new DatabaseStack(app, 'TestDatabaseStack', {
      env: testEnv,
      vpc,
      dbSecurityGroup,
      encryptionKey,
      envName: 'dev',
    });

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });

  it('AgentCoreStack 快照匹配', () => {
    const app = new cdk.App();
    const vpcStack = new cdk.Stack(app, 'VpcStack', { env: testEnv });
    const vpc = createTestVpc(vpcStack);

    const stack = new AgentCoreStack(app, 'TestAgentCoreStack', {
      env: testEnv,
      vpc,
      envName: 'dev',
    });

    expect(Template.fromStack(stack).toJSON()).toMatchSnapshot();
  });
});

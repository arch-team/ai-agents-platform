import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import { Template } from 'aws-cdk-lib/assertions';
import { NetworkStack, SecurityStack, DatabaseStack } from '../../lib/stacks';

const testEnv = { account: '000000000000', region: 'ap-northeast-1' };

// 辅助函数: 创建含 Isolated 子网的 VPC
function createTestVpc(stack: cdk.Stack) {
  return new ec2.Vpc(stack, 'TestVpc', {
    subnetConfiguration: [
      { name: 'Public', subnetType: ec2.SubnetType.PUBLIC, cidrMask: 24 },
      { name: 'Private', subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS, cidrMask: 24 },
      { name: 'Isolated', subnetType: ec2.SubnetType.PRIVATE_ISOLATED, cidrMask: 24 },
    ],
  });
}

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
    const dbSecurityGroup = new ec2.SecurityGroup(vpcStack, 'TestDbSg', { vpc });
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
});

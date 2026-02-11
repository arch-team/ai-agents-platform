import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import type { NetworkStackProps } from '../../lib/stacks/network-stack';
import { NetworkStack } from '../../lib/stacks/network-stack';
import { TEST_ENV, TEST_VPC_CIDR } from '../helpers/test-utils';

describe('NetworkStack', () => {
  const defaultProps: NetworkStackProps = {
    env: TEST_ENV,
    vpcCidr: TEST_VPC_CIDR,
    envName: 'dev',
  };

  it('应创建 VPC', () => {
    const app = new cdk.App();
    const stack = new NetworkStack(app, 'TestNetworkStack', defaultProps);
    const template = Template.fromStack(stack);

    template.hasResourceProperties('AWS::EC2::VPC', {
      CidrBlock: '10.0.0.0/16',
    });
  });

  it('Prod 环境应使用 3 个 NAT Gateway', () => {
    const app = new cdk.App();
    const stack = new NetworkStack(app, 'ProdNetworkStack', {
      ...defaultProps,
      envName: 'prod',
    });
    const template = Template.fromStack(stack);

    template.resourceCountIs('AWS::EC2::NatGateway', 3);
  });

  it('Dev 环境默认应使用 1 个 NAT Gateway', () => {
    const app = new cdk.App();
    const stack = new NetworkStack(app, 'DevNetworkStack', defaultProps);
    const template = Template.fromStack(stack);

    template.resourceCountIs('AWS::EC2::NatGateway', 1);
  });

  it('应输出 VpcId', () => {
    const app = new cdk.App();
    const stack = new NetworkStack(app, 'OutputStack', defaultProps);
    const template = Template.fromStack(stack);

    template.hasOutput('VpcId', {
      Description: 'VPC ID',
    });
  });
});

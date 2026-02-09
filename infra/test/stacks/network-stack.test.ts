import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { NetworkStack } from '../../lib/stacks/network-stack';

describe('NetworkStack', () => {
  const defaultProps = {
    env: { account: '000000000000', region: 'ap-northeast-1' },
    vpcCidr: '10.0.0.0/16',
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

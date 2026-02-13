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

  let template: Template;

  beforeEach(() => {
    const app = new cdk.App();
    const stack = new NetworkStack(app, 'TestNetworkStack', defaultProps);
    template = Template.fromStack(stack);
  });

  it('应创建 VPC', () => {
    template.hasResourceProperties('AWS::EC2::VPC', {
      CidrBlock: '10.0.0.0/16',
    });
  });

  it('Dev 环境默认应使用 1 个 NAT Gateway', () => {
    template.resourceCountIs('AWS::EC2::NatGateway', 1);
  });

  it('应输出 VpcId', () => {
    template.hasOutput('VpcId', {
      Description: 'VPC ID',
    });
  });

  it('Prod 环境默认应使用 1 个 NAT Gateway (初期降低成本)', () => {
    const app = new cdk.App();
    const stack = new NetworkStack(app, 'ProdNetworkStack', {
      ...defaultProps,
      envName: 'prod',
    });
    const prodTemplate = Template.fromStack(stack);

    prodTemplate.resourceCountIs('AWS::EC2::NatGateway', 1);
  });

  it('可通过 natGateways 参数自定义 NAT Gateway 数量', () => {
    const app = new cdk.App();
    const stack = new NetworkStack(app, 'CustomNatStack', {
      ...defaultProps,
      natGateways: 3,
    });
    const customTemplate = Template.fromStack(stack);

    customTemplate.resourceCountIs('AWS::EC2::NatGateway', 3);
  });
});

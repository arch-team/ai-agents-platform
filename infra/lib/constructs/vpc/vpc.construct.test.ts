import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { VpcConstruct } from './vpc.construct';

describe('VpcConstruct', () => {
  let template: Template;

  beforeEach(() => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, 'TestStack');
    new VpcConstruct(stack, 'TestVpc', { vpcCidr: '10.0.0.0/16', envName: 'dev' });
    template = Template.fromStack(stack);
  });

  it('应创建 VPC 且 CIDR 正确', () => {
    template.hasResourceProperties('AWS::EC2::VPC', {
      CidrBlock: '10.0.0.0/16',
    });
  });

  it('应启用 DNS Hostnames 和 DNS Support', () => {
    template.hasResourceProperties('AWS::EC2::VPC', {
      EnableDnsHostnames: true,
      EnableDnsSupport: true,
    });
  });

  it('应创建 Public 子网', () => {
    template.hasResourceProperties('AWS::EC2::Subnet', {
      MapPublicIpOnLaunch: true,
    });
  });

  it('应创建 3 种子网类型 (Public, Private, Isolated)', () => {
    // CDK 测试环境默认 2 AZ，每种子网 2 个 = 6 个子网
    template.resourceCountIs('AWS::EC2::Subnet', 6);
  });

  it('默认应创建 1 个 NAT Gateway', () => {
    template.resourceCountIs('AWS::EC2::NatGateway', 1);
  });

  it('应支持自定义 NAT Gateway 数量', () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, 'CustomNatStack');
    new VpcConstruct(stack, 'TestVpc', {
      vpcCidr: '10.0.0.0/16',
      envName: 'dev',
      natGateways: 2,
    });
    const customTemplate = Template.fromStack(stack);
    customTemplate.resourceCountIs('AWS::EC2::NatGateway', 2);
  });

  it('应创建 S3 Gateway Endpoint', () => {
    template.hasResourceProperties('AWS::EC2::VPCEndpoint', {
      VpcEndpointType: 'Gateway',
    });
  });

  it('默认应创建 VPC Flow Log', () => {
    template.hasResourceProperties('AWS::EC2::FlowLog', {
      ResourceType: 'VPC',
      TrafficType: 'ALL',
    });
  });

  it('Flow Log 应有显式 LogGroup 且保留 1 周 (Dev)', () => {
    template.hasResourceProperties('AWS::Logs::LogGroup', {
      LogGroupName: '/vpc/ai-agents-platform/dev/flow-logs',
      RetentionInDays: 7,
    });
  });

  it('应支持禁用 Flow Log', () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, 'NoFlowLogStack');
    new VpcConstruct(stack, 'TestVpc', {
      vpcCidr: '10.0.0.0/16',
      envName: 'dev',
      enableFlowLog: false,
    });
    const noFlowLogTemplate = Template.fromStack(stack);
    noFlowLogTemplate.resourceCountIs('AWS::EC2::FlowLog', 0);
  });
});

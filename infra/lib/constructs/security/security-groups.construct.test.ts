import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { SecurityGroupsConstruct } from './security-groups.construct';

describe('SecurityGroupsConstruct', () => {
  let template: Template;
  let construct: SecurityGroupsConstruct;

  beforeEach(() => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, 'TestStack');
    const vpc = new ec2.Vpc(stack, 'TestVpc');
    construct = new SecurityGroupsConstruct(stack, 'TestSg', { vpc });
    template = Template.fromStack(stack);
  });

  it('应创建 API 服务安全组', () => {
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      GroupDescription: 'API 服务安全组',
    });
  });

  it('应创建数据库安全组', () => {
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      GroupDescription: '数据库安全组 - 仅允许 API 服务访问',
    });
  });

  it('应创建两个安全组 (不含 VPC 默认安全组)', () => {
    // SecurityGroupsConstruct 创建 ApiSg 和 DbSg 两个安全组
    template.resourceCountIs('AWS::EC2::SecurityGroup', 2);
  });

  it('默认不应添加公网 HTTPS 入站规则', () => {
    // enablePublicIngress 默认为 false，不应有 0.0.0.0/0 入站规则
    const sgResources = template.findResources('AWS::EC2::SecurityGroup', {
      Properties: {
        GroupDescription: 'API 服务安全组',
      },
    });
    const apiSg = Object.values(sgResources)[0];
    expect(apiSg.Properties.SecurityGroupIngress).toBeUndefined();
  });

  it('enablePublicIngress 为 true 时应允许 HTTPS (443) 入站', () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, 'TestStackPublic');
    const vpc = new ec2.Vpc(stack, 'TestVpc');
    new SecurityGroupsConstruct(stack, 'TestSg', { vpc, enablePublicIngress: true });
    const publicTemplate = Template.fromStack(stack);

    publicTemplate.hasResourceProperties('AWS::EC2::SecurityGroup', {
      GroupDescription: 'API 服务安全组',
      SecurityGroupIngress: Match.arrayWith([
        Match.objectLike({
          IpProtocol: 'tcp',
          FromPort: 443,
          ToPort: 443,
          CidrIp: '0.0.0.0/0',
        }),
      ]),
    });
  });

  it('数据库安全组应仅允许 API 安全组的 3306 端口入站', () => {
    // 验证存在从 API SG 到 DB SG 的入站规则 (SecurityGroupIngress)
    template.hasResourceProperties('AWS::EC2::SecurityGroupIngress', {
      IpProtocol: 'tcp',
      FromPort: 3306,
      ToPort: 3306,
    });
  });

  it('数据库安全组应限制出站流量', () => {
    // allowAllOutbound: false 意味着 CDK 不会添加默认的 0.0.0.0/0 出站规则
    // 验证 DB SG 的 SecurityGroupEgress 不包含 0.0.0.0/0 的全端口出站规则
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      GroupDescription: '数据库安全组 - 仅允许 API 服务访问',
      SecurityGroupEgress: Match.arrayWith([
        Match.objectLike({
          CidrIp: '255.255.255.255/32',
          Description: 'Disallow all traffic',
          IpProtocol: 'icmp',
          FromPort: 252,
          ToPort: 86,
        }),
      ]),
    });
  });

  describe('公开属性', () => {
    it('应暴露 apiSecurityGroup', () => {
      expect(construct.apiSecurityGroup).toBeDefined();
    });

    it('应暴露 dbSecurityGroup', () => {
      expect(construct.dbSecurityGroup).toBeDefined();
    });
  });
});

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
      GroupDescription: 'API service security group',
    });
  });

  it('应创建数据库安全组', () => {
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      GroupDescription: 'Database security group - API service access only',
    });
  });

  it('应创建两个安全组 (API + DB)', () => {
    template.resourceCountIs('AWS::EC2::SecurityGroup', 2);
  });

  it('默认不应添加公网 HTTPS 入站规则', () => {
    const sgResources = template.findResources('AWS::EC2::SecurityGroup', {
      Properties: {
        GroupDescription: 'API service security group',
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
      GroupDescription: 'API service security group',
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
    template.hasResourceProperties('AWS::EC2::SecurityGroupIngress', {
      IpProtocol: 'tcp',
      FromPort: 3306,
      ToPort: 3306,
    });
  });

  it('数据库安全组应限制出站流量', () => {
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      GroupDescription: 'Database security group - API service access only',
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

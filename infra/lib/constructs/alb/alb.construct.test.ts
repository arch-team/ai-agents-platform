import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { createTestVpc } from '../../../test/helpers/test-utils';
import { AlbConstruct } from './alb.construct';

describe('AlbConstruct', () => {
  let template: Template;

  beforeEach(() => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, 'TestStack');
    const vpc = createTestVpc(stack);

    new AlbConstruct(stack, 'TestAlb', {
      vpc,
      envName: 'dev',
    });
    template = Template.fromStack(stack);
  });

  it('应创建 Application Load Balancer (internet-facing)', () => {
    template.hasResourceProperties('AWS::ElasticLoadBalancingV2::LoadBalancer', {
      Scheme: 'internet-facing',
      Type: 'application',
      Name: 'ai-agents-dev',
    });
  });

  it('应创建 ALB 安全组并允许 HTTP 入站', () => {
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      GroupDescription: 'ALB security group - public HTTP ingress',
    });
  });

  it('安全组应允许 0.0.0.0/0 的 80 端口入站', () => {
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      SecurityGroupIngress: Match.arrayWith([
        Match.objectLike({
          CidrIp: '0.0.0.0/0',
          FromPort: 80,
          ToPort: 80,
          IpProtocol: 'tcp',
        }),
      ]),
    });
  });

  it('应创建 HTTP Listener (端口 80)', () => {
    template.hasResourceProperties('AWS::ElasticLoadBalancingV2::Listener', {
      Port: 80,
      Protocol: 'HTTP',
    });
  });

  it('应创建 Target Group (端口 8000, HTTP)', () => {
    template.hasResourceProperties('AWS::ElasticLoadBalancingV2::TargetGroup', {
      Port: 8000,
      Protocol: 'HTTP',
      TargetType: 'ip',
    });
  });

  it('Target Group 应配置健康检查 (/health)', () => {
    template.hasResourceProperties('AWS::ElasticLoadBalancingV2::TargetGroup', {
      HealthCheckPath: '/health',
      HealthCheckIntervalSeconds: 30,
    });
  });

  describe('公开属性', () => {
    it('应暴露 alb, albSecurityGroup, httpListener, targetGroup', () => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const vpc = createTestVpc(stack);

      const albConstruct = new AlbConstruct(stack, 'TestAlb', {
        vpc,
        envName: 'dev',
      });

      expect(albConstruct.alb).toBeDefined();
      expect(albConstruct.albSecurityGroup).toBeDefined();
      expect(albConstruct.httpListener).toBeDefined();
      expect(albConstruct.targetGroup).toBeDefined();
    });
  });
});

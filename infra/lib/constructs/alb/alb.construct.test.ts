import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { createTestVpc } from '../../../test/helpers/test-utils';
import { AlbConstruct } from './alb.construct';

describe('AlbConstruct', () => {
  describe('默认配置 (HTTP-only, 无 ECS 安全组)', () => {
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

    it('应创建 ALB 安全组 (allowAllOutbound: false)', () => {
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
  });

  describe('传入 ECS 安全组时', () => {
    it('应创建 ALB → ECS 的显式出站规则', () => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const vpc = createTestVpc(stack);
      const ecsSg = new ec2.SecurityGroup(stack, 'EcsSg', { vpc });

      new AlbConstruct(stack, 'TestAlb', {
        vpc,
        envName: 'dev',
        ecsSecurityGroup: ecsSg,
        containerPort: 8000,
      });
      const template = Template.fromStack(stack);

      template.hasResourceProperties('AWS::EC2::SecurityGroupEgress', {
        IpProtocol: 'tcp',
        FromPort: 8000,
        ToPort: 8000,
        Description: 'Allow ALB to forward traffic to ECS containers',
      });
    });
  });

  describe('HTTPS 模式 (提供 certificateArn)', () => {
    let template: Template;

    beforeEach(() => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const vpc = createTestVpc(stack);

      new AlbConstruct(stack, 'TestAlb', {
        vpc,
        envName: 'prod',
        certificateArn: 'arn:aws:acm:us-east-1:123456789012:certificate/test-cert',
      });
      template = Template.fromStack(stack);
    });

    it('应创建 HTTPS Listener (端口 443)', () => {
      template.hasResourceProperties('AWS::ElasticLoadBalancingV2::Listener', {
        Port: 443,
        Protocol: 'HTTPS',
        SslPolicy: 'ELBSecurityPolicy-TLS-1-2-2017-01',
      });
    });

    it('HTTP Listener 应重定向到 HTTPS', () => {
      template.hasResourceProperties('AWS::ElasticLoadBalancingV2::Listener', {
        Port: 80,
        Protocol: 'HTTP',
        DefaultActions: Match.arrayWith([
          Match.objectLike({
            Type: 'redirect',
            RedirectConfig: Match.objectLike({
              Protocol: 'HTTPS',
              Port: '443',
              StatusCode: 'HTTP_301',
            }),
          }),
        ]),
      });
    });

    it('安全组应同时允许 HTTP 和 HTTPS 入站', () => {
      template.hasResourceProperties('AWS::EC2::SecurityGroup', {
        SecurityGroupIngress: Match.arrayWith([
          Match.objectLike({ FromPort: 80, ToPort: 80, IpProtocol: 'tcp' }),
          Match.objectLike({ FromPort: 443, ToPort: 443, IpProtocol: 'tcp' }),
        ]),
      });
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
      expect(albConstruct.httpsListener).toBeUndefined();
    });

    it('提供 certificateArn 时应暴露 httpsListener', () => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const vpc = createTestVpc(stack);

      const albConstruct = new AlbConstruct(stack, 'TestAlb', {
        vpc,
        envName: 'prod',
        certificateArn: 'arn:aws:acm:us-east-1:123456789012:certificate/test-cert',
      });

      expect(albConstruct.httpsListener).toBeDefined();
    });
  });
});

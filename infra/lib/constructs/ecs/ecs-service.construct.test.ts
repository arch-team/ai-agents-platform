import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import { createTestVpc } from '../../../test/helpers/test-utils';
import { EcsServiceConstruct } from './ecs-service.construct';

/** 创建 ECS Construct 测试依赖 */
function createEcsDependencies(stack: cdk.Stack) {
  const vpc = createTestVpc(stack);
  const albSecurityGroup = new ec2.SecurityGroup(stack, 'AlbSg', { vpc });
  const containerImage = ecs.ContainerImage.fromRegistry('amazon/amazon-ecs-sample');
  return { vpc, albSecurityGroup, containerImage };
}

describe('EcsServiceConstruct', () => {
  describe('默认配置', () => {
    let template: Template;

    beforeEach(() => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const { vpc, albSecurityGroup, containerImage } = createEcsDependencies(stack);

      new EcsServiceConstruct(stack, 'TestEcs', {
        vpc,
        albSecurityGroup,
        envName: 'dev',
        containerImage,
      });
      template = Template.fromStack(stack);
    });

    it('应创建 ECS 集群', () => {
      template.hasResourceProperties('AWS::ECS::Cluster', {
        ClusterName: 'ai-agents-dev',
      });
    });

    it('应启用 Container Insights', () => {
      template.hasResourceProperties('AWS::ECS::Cluster', {
        ClusterSettings: Match.arrayWith([
          Match.objectLike({
            Name: 'containerInsights',
            Value: 'enabled',
          }),
        ]),
      });
    });

    it('应创建 Fargate Task Definition (256 CPU, 512 MiB)', () => {
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        Cpu: '256',
        Memory: '512',
        RequiresCompatibilities: ['FARGATE'],
        NetworkMode: 'awsvpc',
      });
    });

    it('应创建容器定义 (端口 8000)', () => {
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        ContainerDefinitions: Match.arrayWith([
          Match.objectLike({
            Name: 'api',
            PortMappings: Match.arrayWith([Match.objectLike({ ContainerPort: 8000 })]),
          }),
        ]),
      });
    });

    it('容器应配置健康检查', () => {
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        ContainerDefinitions: Match.arrayWith([
          Match.objectLike({
            HealthCheck: Match.objectLike({
              Command: Match.arrayWith([
                'CMD-SHELL',
                'curl -f http://localhost:8000/health || exit 1',
              ]),
            }),
          }),
        ]),
      });
    });

    it('应创建 Fargate Service (desiredCount: 1)', () => {
      template.hasResourceProperties('AWS::ECS::Service', {
        DesiredCount: 1,
        LaunchType: 'FARGATE',
      });
    });

    it('服务不应分配公网 IP', () => {
      template.hasResourceProperties('AWS::ECS::Service', {
        NetworkConfiguration: Match.objectLike({
          AwsvpcConfiguration: Match.objectLike({
            AssignPublicIp: 'DISABLED',
          }),
        }),
      });
    });

    it('应创建 CloudWatch 日志组 (保留 1 周)', () => {
      template.hasResourceProperties('AWS::Logs::LogGroup', {
        LogGroupName: '/ecs/ai-agents-platform/dev',
        RetentionInDays: 7,
      });
    });

    it('应创建 ECS 服务安全组', () => {
      template.hasResourceProperties('AWS::EC2::SecurityGroup', {
        GroupDescription: 'ECS Fargate service security group - ALB ingress only',
      });
    });
  });

  describe('自定义参数', () => {
    it('应支持自定义 desiredCount', () => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const { vpc, albSecurityGroup, containerImage } = createEcsDependencies(stack);

      new EcsServiceConstruct(stack, 'TestEcs', {
        vpc,
        albSecurityGroup,
        envName: 'prod',
        containerImage,
        desiredCount: 3,
      });
      const template = Template.fromStack(stack);

      template.hasResourceProperties('AWS::ECS::Service', {
        DesiredCount: 3,
      });
    });

    it('应支持自定义环境变量', () => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const { vpc, albSecurityGroup, containerImage } = createEcsDependencies(stack);

      new EcsServiceConstruct(stack, 'TestEcs', {
        vpc,
        albSecurityGroup,
        envName: 'dev',
        containerImage,
        environment: { DATABASE_HOST: 'localhost' },
      });
      const template = Template.fromStack(stack);

      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        ContainerDefinitions: Match.arrayWith([
          Match.objectLike({
            Environment: Match.arrayWith([
              Match.objectLike({ Name: 'DATABASE_HOST', Value: 'localhost' }),
            ]),
          }),
        ]),
      });
    });
  });

  describe('公开属性', () => {
    it('应暴露 cluster, service, serviceSecurityGroup, containerPort', () => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const { vpc, albSecurityGroup, containerImage } = createEcsDependencies(stack);

      const ecsConstruct = new EcsServiceConstruct(stack, 'TestEcs', {
        vpc,
        albSecurityGroup,
        envName: 'dev',
        containerImage,
      });

      expect(ecsConstruct.cluster).toBeDefined();
      expect(ecsConstruct.service).toBeDefined();
      expect(ecsConstruct.serviceSecurityGroup).toBeDefined();
      expect(ecsConstruct.containerPort).toBe(8000);
    });
  });
});

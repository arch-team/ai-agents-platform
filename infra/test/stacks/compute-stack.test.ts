import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { ComputeStack } from '../../lib/stacks/compute-stack';
import { createTestVpc } from '../helpers/test-utils';

/** 创建 ComputeStack 跨 Stack 测试依赖 */
function createComputeDependencies(app: cdk.App) {
  const depsStack = new cdk.Stack(app, 'DepsStack');
  const vpc = createTestVpc(depsStack);
  const dbSecurityGroup = new ec2.SecurityGroup(depsStack, 'DbSg', {
    vpc,
    allowAllOutbound: false,
  });
  const encryptionKey = new kms.Key(depsStack, 'Key');
  const databaseSecret = new secretsmanager.Secret(depsStack, 'DbSecret');
  const databaseEndpoint = 'test-cluster.cluster-xyz.us-east-1.rds.amazonaws.com';

  return { vpc, dbSecurityGroup, databaseSecret, databaseEndpoint, encryptionKey };
}

describe('ComputeStack', () => {
  let template: Template;
  let stack: ComputeStack;

  beforeEach(() => {
    const app = new cdk.App();
    const { vpc, dbSecurityGroup, databaseSecret, databaseEndpoint, encryptionKey } =
      createComputeDependencies(app);

    stack = new ComputeStack(app, 'TestComputeStack', {
      vpc,
      dbSecurityGroup,
      databaseSecret,
      databaseEndpoint,
      encryptionKey,
      envName: 'dev',
    });
    template = Template.fromStack(stack);
  });

  describe('ALB', () => {
    it('应创建 internet-facing ALB', () => {
      template.hasResourceProperties('AWS::ElasticLoadBalancingV2::LoadBalancer', {
        Scheme: 'internet-facing',
        Type: 'application',
      });
    });

    it('应创建 HTTP Listener (端口 80)', () => {
      template.hasResourceProperties('AWS::ElasticLoadBalancingV2::Listener', {
        Port: 80,
        Protocol: 'HTTP',
      });
    });

    it('应创建 Target Group (端口 8000)', () => {
      template.hasResourceProperties('AWS::ElasticLoadBalancingV2::TargetGroup', {
        Port: 8000,
        Protocol: 'HTTP',
        TargetType: 'ip',
        HealthCheckPath: '/health',
      });
    });
  });

  describe('ECS', () => {
    it('应创建 ECS 集群', () => {
      template.hasResourceProperties('AWS::ECS::Cluster', {
        ClusterName: 'ai-agents-dev',
      });
    });

    it('应创建 Fargate Task Definition (256 CPU, 512 MiB)', () => {
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        Cpu: '256',
        Memory: '512',
        RequiresCompatibilities: ['FARGATE'],
      });
    });

    it('应创建 Fargate Service', () => {
      template.hasResourceProperties('AWS::ECS::Service', {
        DesiredCount: 1,
        LaunchType: 'FARGATE',
      });
    });

    it('应创建 CloudWatch 日志组', () => {
      template.hasResourceProperties('AWS::Logs::LogGroup', {
        LogGroupName: '/ecs/ai-agents-platform/dev',
        RetentionInDays: 7,
      });
    });

    it('容器应注入数据库环境变量', () => {
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        ContainerDefinitions: Match.arrayWith([
          Match.objectLike({
            Environment: Match.arrayWith([
              Match.objectLike({ Name: 'ENV_NAME', Value: 'dev' }),
              Match.objectLike({ Name: 'DATABASE_HOST' }),
              Match.objectLike({ Name: 'DATABASE_PORT', Value: '3306' }),
            ]),
          }),
        ]),
      });
    });

    it('容器应注入数据库 Secret', () => {
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        ContainerDefinitions: Match.arrayWith([
          Match.objectLike({
            Secrets: Match.arrayWith([Match.objectLike({ Name: 'DATABASE_SECRET' })]),
          }),
        ]),
      });
    });
  });

  describe('安全组', () => {
    it('应创建 ALB 安全组 (允许 HTTP 入站)', () => {
      template.hasResourceProperties('AWS::EC2::SecurityGroup', {
        GroupDescription: 'ALB security group - public HTTP ingress',
      });
    });

    it('应创建 ECS 服务安全组', () => {
      template.hasResourceProperties('AWS::EC2::SecurityGroup', {
        GroupDescription: 'ECS Fargate service security group - ALB ingress only',
      });
    });
  });

  describe('Outputs', () => {
    it('应输出 AlbDnsName', () => {
      template.hasOutput('AlbDnsName', {
        Description: 'ALB DNS name',
      });
    });

    it('应输出 EcsClusterName', () => {
      template.hasOutput('EcsClusterName', {
        Description: 'ECS cluster name',
      });
    });

    it('应输出 ServiceName', () => {
      template.hasOutput('ServiceName', {
        Description: 'ECS service name',
      });
    });
  });

  describe('公开属性', () => {
    it('应暴露 albDnsName 和 service', () => {
      expect(stack.albDnsName).toBeDefined();
      expect(stack.service).toBeDefined();
    });
  });
});

import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { ComputeStack } from '../../lib/stacks/compute-stack';
import { createCrossStackComputeDependencies } from '../helpers/test-utils';

describe('ComputeStack', () => {
  let template: Template;
  let stack: ComputeStack;

  beforeEach(() => {
    const app = new cdk.App();
    const {
      vpc,
      dbSecurityGroup,
      databaseSecret,
      jwtSecretArn,
      databaseEndpoint,
      encryptionKeyArn,
    } = createCrossStackComputeDependencies(app);

    stack = new ComputeStack(app, 'TestComputeStack', {
      vpc,
      dbSecurityGroup,
      databaseSecret,
      databaseEndpoint,
      encryptionKeyArn,
      jwtSecretArn,
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
              Match.objectLike({ Name: 'APP_ENV', Value: 'development' }),
              Match.objectLike({ Name: 'DATABASE_HOST' }),
              Match.objectLike({ Name: 'DATABASE_PORT', Value: '3306' }),
              Match.objectLike({ Name: 'DB_SECRET_ARN' }),
              Match.objectLike({ Name: 'JWT_SECRET_ARN' }),
            ]),
          }),
        ]),
      });
    });

    it('容器应注入 Claude Agent SDK 所需环境变量', () => {
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        ContainerDefinitions: Match.arrayWith([
          Match.objectLike({
            Environment: Match.arrayWith([
              Match.objectLike({ Name: 'CLAUDE_CODE_USE_BEDROCK', Value: '1' }),
            ]),
          }),
        ]),
      });
    });

    it('AGENT_RUNTIME_MODE 默认为 in_process', () => {
      // beforeEach 未传 agentRuntimeMode，应使用默认值 'in_process'
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        ContainerDefinitions: Match.arrayWith([
          Match.objectLike({
            Environment: Match.arrayWith([
              Match.objectLike({ Name: 'AGENT_RUNTIME_MODE', Value: 'in_process' }),
            ]),
          }),
        ]),
      });
    });

    it('AGENT_RUNTIME_MODE 应从 Props 读取配置值', () => {
      const app = new cdk.App();
      const deps = createCrossStackComputeDependencies(app);

      const customStack = new ComputeStack(app, 'TestComputeStackCustomMode', {
        ...deps,
        envName: 'dev',
        agentRuntimeMode: 'agentcore_runtime',
      });
      const customTemplate = Template.fromStack(customStack);

      customTemplate.hasResourceProperties('AWS::ECS::TaskDefinition', {
        ContainerDefinitions: Match.arrayWith([
          Match.objectLike({
            Environment: Match.arrayWith([
              Match.objectLike({ Name: 'AGENT_RUNTIME_MODE', Value: 'agentcore_runtime' }),
            ]),
          }),
        ]),
      });
    });

    it('容器应注入 Secrets Manager 凭证', () => {
      template.hasResourceProperties('AWS::ECS::TaskDefinition', {
        ContainerDefinitions: Match.arrayWith([
          Match.objectLike({
            Secrets: Match.arrayWith([
              Match.objectLike({ Name: 'DATABASE_USER' }),
              Match.objectLike({ Name: 'DATABASE_PASSWORD' }),
              Match.objectLike({ Name: 'DATABASE_NAME' }),
              Match.objectLike({ Name: 'JWT_SECRET_KEY' }),
            ]),
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

  describe('Bedrock Eval IAM', () => {
    it('ECS Task Role 应包含 Bedrock 评估 Pipeline IAM 权限', () => {
      template.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: Match.arrayWith([
                'bedrock:CreateModelEvaluationJob',
                'bedrock:GetModelEvaluationJob',
                'bedrock:ListModelEvaluationJobs',
                'bedrock:StopModelEvaluationJob',
              ]),
              Effect: 'Allow',
            }),
          ]),
        },
      });
    });
  });

  describe('Eval Trigger Lambda', () => {
    it('应创建评估触发 Lambda 函数 (Python 3.14, ARM_64)', () => {
      template.hasResourceProperties('AWS::Lambda::Function', {
        FunctionName: 'ai-agents-platform-eval-trigger-dev',
        Runtime: 'python3.13',
        Architectures: ['arm64'],
        Timeout: 60,
        MemorySize: 128,
        TracingConfig: { Mode: 'Active' },
      });
    });

    it('Lambda 应配置 API_BASE_URL 环境变量', () => {
      template.hasResourceProperties('AWS::Lambda::Function', {
        Environment: {
          Variables: Match.objectLike({
            API_BASE_URL: Match.anyValue(),
          }),
        },
      });
    });

    it('应创建 Lambda CloudWatch 日志组', () => {
      template.hasResourceProperties('AWS::Logs::LogGroup', {
        LogGroupName: '/aws/lambda/ai-agents-platform-eval-trigger-dev',
        RetentionInDays: 7,
      });
    });
  });

  describe('EventBridge Schedule Rule', () => {
    it('应创建评估定时触发规则', () => {
      template.hasResourceProperties('AWS::Events::Rule', {
        Name: 'ai-agents-platform-eval-trigger-dev',
        ScheduleExpression: 'cron(0 2 * * ? *)',
        State: 'DISABLED',
      });
    });

    it('Prod 环境规则应启用', () => {
      const app = new cdk.App();
      const deps = createCrossStackComputeDependencies(app);

      const prodStack = new ComputeStack(app, 'TestComputeStackProd', {
        ...deps,
        envName: 'prod',
      });
      const prodTemplate = Template.fromStack(prodStack);

      prodTemplate.hasResourceProperties('AWS::Events::Rule', {
        Name: 'ai-agents-platform-eval-trigger-prod',
        State: 'ENABLED',
      });
    });
  });

  describe('定时缩放', () => {
    it('配置 scheduledScaling 时应创建 ScalableTarget 和 2 个 ScheduledAction', () => {
      const app = new cdk.App();
      const deps = createCrossStackComputeDependencies(app);

      const stackWithScaling = new ComputeStack(app, 'TestComputeStackScaling', {
        ...deps,
        envName: 'dev',
        scheduledScaling: {
          scaleDownSchedule: '0 12 * * ? *',
          scaleUpSchedule: '0 0 * * ? *',
          scaleUpMinCapacity: 1,
          scaleUpMaxCapacity: 1,
        },
      });
      const tmpl = Template.fromStack(stackWithScaling);

      // 应创建 ScalableTarget (Application Auto Scaling)
      tmpl.hasResourceProperties('AWS::ApplicationAutoScaling::ScalableTarget', {
        MinCapacity: 0,
        MaxCapacity: 1,
        ScalableDimension: 'ecs:service:DesiredCount',
        ServiceNamespace: 'ecs',
      });

      // 应创建 2 个 ScheduledAction (缩减 + 恢复)
      tmpl.resourceCountIs('AWS::ApplicationAutoScaling::ScalableTarget', 1);

      // 验证缩减 ScheduledAction
      tmpl.hasResourceProperties('AWS::ApplicationAutoScaling::ScalableTarget', {
        ScheduledActions: Match.arrayWith([
          Match.objectLike({
            ScalableTargetAction: { MinCapacity: 0, MaxCapacity: 0 },
            Schedule: 'cron(0 12 * * ? *)',
            ScheduledActionName: 'ScaleDown',
          }),
          Match.objectLike({
            ScalableTargetAction: { MinCapacity: 1, MaxCapacity: 1 },
            Schedule: 'cron(0 0 * * ? *)',
            ScheduledActionName: 'ScaleUp',
          }),
        ]),
      });
    });

    it('未配置 scheduledScaling 时不应创建缩放资源', () => {
      // 使用 beforeEach 中创建的默认 template (未配置 scheduledScaling)
      template.resourceCountIs('AWS::ApplicationAutoScaling::ScalableTarget', 0);
    });
  });
});

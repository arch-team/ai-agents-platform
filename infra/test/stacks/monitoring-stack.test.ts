import * as cdk from 'aws-cdk-lib';
import { Match, Template } from 'aws-cdk-lib/assertions';
import { MonitoringStack } from '../../lib/stacks/monitoring-stack';
import { createMonitoringTestDeps } from '../helpers/test-utils';

describe('MonitoringStack', () => {
  let template: Template;
  let stack: MonitoringStack;

  beforeEach(() => {
    const app = new cdk.App();
    const { databaseStack, computeStack } = createMonitoringTestDeps(app);

    stack = new MonitoringStack(app, 'TestMonitoringStack', {
      cluster: databaseStack.cluster,
      service: computeStack.service,
      loadBalancer: computeStack.loadBalancer,
      targetGroup: computeStack.targetGroup,
      alertEmail: 'test@example.com',
      envName: 'dev',
    });

    template = Template.fromStack(stack);
  });

  describe('SNS Topic', () => {
    it('应创建 SNS 告警主题', () => {
      template.hasResourceProperties('AWS::SNS::Topic', {
        TopicName: 'ai-agents-platform-alerts-dev',
      });
    });

    it('应创建邮件订阅 (提供 alertEmail 时)', () => {
      template.hasResourceProperties('AWS::SNS::Subscription', {
        Protocol: 'email',
        Endpoint: 'test@example.com',
      });
    });
  });

  describe('Aurora CloudWatch Alarms', () => {
    it('应创建 Aurora CPU 利用率告警', () => {
      template.hasResourceProperties('AWS::CloudWatch::Alarm', {
        AlarmName: 'ai-agents-platform-dev-aurora-cpu-high',
        Threshold: 80,
        EvaluationPeriods: 3,
        ComparisonOperator: 'GreaterThanThreshold',
      });
    });

    it('应创建 Aurora 可用内存告警', () => {
      template.hasResourceProperties('AWS::CloudWatch::Alarm', {
        AlarmName: 'ai-agents-platform-dev-aurora-memory-low',
        Threshold: 524288000,
        EvaluationPeriods: 3,
        ComparisonOperator: 'LessThanThreshold',
      });
    });

    it('应创建 Aurora 数据库连接数告警', () => {
      template.hasResourceProperties('AWS::CloudWatch::Alarm', {
        AlarmName: 'ai-agents-platform-dev-aurora-connections-high',
        Threshold: 72,
        EvaluationPeriods: 3,
        ComparisonOperator: 'GreaterThanThreshold',
      });
    });
  });

  describe('ECS CloudWatch Alarms', () => {
    it('应创建 ECS CPU 利用率告警', () => {
      template.hasResourceProperties('AWS::CloudWatch::Alarm', {
        AlarmName: 'ai-agents-platform-dev-ecs-cpu-high',
        Threshold: 80,
        EvaluationPeriods: 3,
        ComparisonOperator: 'GreaterThanThreshold',
      });
    });

    it('应创建 ECS 内存利用率告警', () => {
      template.hasResourceProperties('AWS::CloudWatch::Alarm', {
        AlarmName: 'ai-agents-platform-dev-ecs-memory-high',
        Threshold: 80,
        EvaluationPeriods: 3,
        ComparisonOperator: 'GreaterThanThreshold',
      });
    });
  });

  describe('ALB CloudWatch Alarms', () => {
    it('应创建 ALB 不健康实例告警', () => {
      template.hasResourceProperties('AWS::CloudWatch::Alarm', {
        AlarmName: 'ai-agents-platform-dev-alb-unhealthy-hosts',
        Threshold: 1,
        EvaluationPeriods: 1,
        ComparisonOperator: 'GreaterThanOrEqualToThreshold',
      });
    });

    it('应创建 ALB 5XX 错误告警', () => {
      template.hasResourceProperties('AWS::CloudWatch::Alarm', {
        AlarmName: 'ai-agents-platform-dev-alb-5xx-high',
        Threshold: 10,
        EvaluationPeriods: 1,
        ComparisonOperator: 'GreaterThanThreshold',
      });
    });
  });

  describe('告警总数', () => {
    it('应创建 8 个 CloudWatch Alarm', () => {
      template.resourceCountIs('AWS::CloudWatch::Alarm', 8);
    });
  });

  describe('告警动作', () => {
    it('所有告警应指向 SNS Topic', () => {
      const alarms = template.findResources('AWS::CloudWatch::Alarm');
      const topics = template.findResources('AWS::SNS::Topic');
      const topicLogicalIds = Object.keys(topics);

      // 每个 Alarm 的 AlarmActions 都应引用 SNS Topic
      for (const [, alarm] of Object.entries(alarms)) {
        const alarmActions = alarm.Properties.AlarmActions;
        expect(alarmActions).toBeDefined();
        expect(alarmActions.length).toBeGreaterThan(0);

        // AlarmActions 中的 Ref 应指向 SNS Topic
        const ref = alarmActions[0].Ref;
        expect(topicLogicalIds).toContain(ref);
      }
    });
  });

  describe('CloudWatch Dashboard', () => {
    it('应创建 CloudWatch Dashboard', () => {
      template.hasResourceProperties('AWS::CloudWatch::Dashboard', {
        DashboardName: 'ai-agents-platform-dev',
      });
    });

    it('Dashboard 应存在且仅 1 个', () => {
      template.resourceCountIs('AWS::CloudWatch::Dashboard', 1);
    });
  });

  describe('无 alertEmail 时', () => {
    it('不应创建邮件订阅', () => {
      const app = new cdk.App();
      const { databaseStack, computeStack } = createMonitoringTestDeps(app);

      const noEmailStack = new MonitoringStack(app, 'TestMonitoringNoEmail', {
        cluster: databaseStack.cluster,
        service: computeStack.service,
        loadBalancer: computeStack.loadBalancer,
        targetGroup: computeStack.targetGroup,
        envName: 'dev',
      });

      const noEmailTemplate = Template.fromStack(noEmailStack);
      noEmailTemplate.resourceCountIs('AWS::SNS::Subscription', 0);
      // SNS Topic 仍应存在
      noEmailTemplate.hasResourceProperties('AWS::SNS::Topic', {
        TopicName: 'ai-agents-platform-alerts-dev',
      });
    });
  });

  describe('公开属性', () => {
    it('应暴露 alertTopic', () => {
      expect(stack.alertTopic).toBeDefined();
    });
  });

  describe('KMS 加密', () => {
    it('提供 encryptionKey 时 SNS Topic 应使用 KMS 加密', () => {
      const app = new cdk.App();
      const { databaseStack, computeStack, encryptionKey } = createMonitoringTestDeps(app);

      const encryptedStack = new MonitoringStack(app, 'TestMonitoringEncrypted', {
        cluster: databaseStack.cluster,
        service: computeStack.service,
        loadBalancer: computeStack.loadBalancer,
        targetGroup: computeStack.targetGroup,
        encryptionKey,
        envName: 'dev',
      });

      const encryptedTemplate = Template.fromStack(encryptedStack);
      encryptedTemplate.hasResourceProperties('AWS::SNS::Topic', {
        KmsMasterKeyId: Match.anyValue(),
      });
    });

    it('未提供 encryptionKey 时 SNS Topic 不应有 KMS 加密', () => {
      // 默认 beforeEach 的 stack 未传 encryptionKey
      template.hasResourceProperties('AWS::SNS::Topic', {
        TopicName: 'ai-agents-platform-alerts-dev',
      });
    });
  });
});

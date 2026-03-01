import * as cdk from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as cw_actions from 'aws-cdk-lib/aws-cloudwatch-actions';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as events from 'aws-cdk-lib/aws-events';
import * as events_targets from 'aws-cdk-lib/aws-events-targets';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import { PROJECT_NAME, type BaseStackProps, type EnvironmentName } from '../config';

/** 监控指标统一采样周期 (5 分钟) */
const METRIC_PERIOD = cdk.Duration.minutes(5);

/** 告警默认配置 — 避免各 Alarm 重复声明相同的 evaluationPeriods、treatMissingData 等 */
const ALARM_DEFAULTS = {
  /** 标准评估窗口: 连续 3 个数据点 */
  evaluationPeriods: 3,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
} as const;

export interface MonitoringStackProps extends BaseStackProps {
  /** Aurora 数据库集群 */
  readonly cluster: rds.IDatabaseCluster;
  /** ECS Fargate 服务 */
  readonly service: ecs.FargateService;
  /** Application Load Balancer */
  readonly loadBalancer: elbv2.IApplicationLoadBalancer;
  /** ALB Target Group */
  readonly targetGroup: elbv2.IApplicationTargetGroup;
  /** KMS 加密密钥 — 用于 SNS Topic 加密 @default undefined (不加密) */
  readonly encryptionKey?: kms.IKey;
  /** 告警通知邮箱 @default undefined (不创建邮件订阅) */
  readonly alertEmail?: string;
  /** ECS 服务的 CloudWatch Log Group 名称 @default undefined (不创建日志告警) */
  readonly logGroupName?: string;
}

/**
 * MonitoringStack - 监控和告警基础设施栈。
 * @remarks
 * 包含 SNS 告警主题、Aurora/ECS/ALB CloudWatch Alarms 和 CloudWatch Dashboard。
 * 所有告警动作指向 SNS Topic。
 */
export class MonitoringStack extends cdk.Stack {
  /** SNS 告警主题 */
  public readonly alertTopic: sns.Topic;
  /** 告警动作 (所有 Alarm 共享) */
  private readonly alarmAction: cw_actions.SnsAction;

  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    const { cluster, service, loadBalancer, targetGroup, encryptionKey, alertEmail, envName } =
      props;

    // SNS 告警主题 — 使用 KMS CMK 加密 (如提供)
    this.alertTopic = new sns.Topic(this, 'AlertTopic', {
      topicName: `${PROJECT_NAME}-alerts-${envName}`,
      displayName: `${PROJECT_NAME} ${envName} Alerts`,
      masterKey: encryptionKey,
    });
    this.alarmAction = new cw_actions.SnsAction(this.alertTopic);

    // 如有 alertEmail，添加邮件订阅
    if (alertEmail) {
      this.alertTopic.addSubscription(new subscriptions.EmailSubscription(alertEmail));
    }

    // Aurora CloudWatch Alarms
    this.createAuroraAlarms(cluster, envName);

    // ECS CloudWatch Alarms
    this.createEcsAlarms(service, envName);

    // ALB CloudWatch Alarms
    this.createAlbAlarms(loadBalancer, targetGroup, envName);

    // 应用级错误日志告警 (如提供 Log Group)
    if (props.logGroupName) {
      this.createApplicationErrorAlarm(props.logGroupName, envName);
    }

    // CloudWatch Dashboard
    this.createDashboard(cluster, service, loadBalancer, targetGroup, envName);

    // ECS 部署失败 EventBridge 规则 — 自动发送 SNS 告警
    this.createDeploymentFailureRule(envName);

    // CDK Nag 抑制
    this.suppressNagRules(!!encryptionKey);
  }

  /** 创建 Alarm 并自动绑定告警动作 */
  private createAlarm(id: string, props: cloudwatch.AlarmProps): cloudwatch.Alarm {
    const alarm = new cloudwatch.Alarm(this, id, props);
    alarm.addAlarmAction(this.alarmAction);
    return alarm;
  }

  /** 创建 Aurora 数据库监控告警 */
  private createAuroraAlarms(cluster: rds.IDatabaseCluster, envName: EnvironmentName): void {
    // Aurora CPU 利用率告警 — 连续 3 个 5 分钟数据点超过 80%
    this.createAlarm('AuroraCpuAlarm', {
      alarmName: `${PROJECT_NAME}-${envName}-aurora-cpu-high`,
      alarmDescription: 'Aurora CPU utilization exceeds 80%',
      metric: cluster.metricCPUUtilization({ period: METRIC_PERIOD, statistic: 'Average' }),
      threshold: 80,
      ...ALARM_DEFAULTS,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    });

    // Aurora 可用内存告警 — 低于 500MB
    this.createAlarm('AuroraMemoryAlarm', {
      alarmName: `${PROJECT_NAME}-${envName}-aurora-memory-low`,
      alarmDescription: 'Aurora freeable memory below 500MB',
      metric: cluster.metric('FreeableMemory', { period: METRIC_PERIOD, statistic: 'Average' }),
      threshold: 524288000, // 500MB in bytes
      ...ALARM_DEFAULTS,
      comparisonOperator: cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
    });

    // Aurora 数据库连接数告警 — 超过最大连接数 80% (db.t3.medium 默认约 90)
    this.createAlarm('AuroraConnectionsAlarm', {
      alarmName: `${PROJECT_NAME}-${envName}-aurora-connections-high`,
      alarmDescription: 'Aurora database connections exceed 80% of max',
      metric: cluster.metric('DatabaseConnections', {
        period: METRIC_PERIOD,
        statistic: 'Average',
      }),
      threshold: 72, // 90 * 0.8 = 72
      ...ALARM_DEFAULTS,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    });
  }

  /** 创建 ECS 服务监控告警 */
  private createEcsAlarms(service: ecs.FargateService, envName: EnvironmentName): void {
    // ECS CPU 利用率告警 — 连续 3 个 5 分钟数据点超过 80%
    this.createAlarm('EcsCpuAlarm', {
      alarmName: `${PROJECT_NAME}-${envName}-ecs-cpu-high`,
      alarmDescription: 'ECS service CPU utilization exceeds 80%',
      metric: service.metricCpuUtilization({ period: METRIC_PERIOD, statistic: 'Average' }),
      threshold: 80,
      ...ALARM_DEFAULTS,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    });

    // ECS 内存利用率告警 — 连续 3 个 5 分钟数据点超过 80%
    this.createAlarm('EcsMemoryAlarm', {
      alarmName: `${PROJECT_NAME}-${envName}-ecs-memory-high`,
      alarmDescription: 'ECS service memory utilization exceeds 80%',
      metric: service.metricMemoryUtilization({ period: METRIC_PERIOD, statistic: 'Average' }),
      threshold: 80,
      ...ALARM_DEFAULTS,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    });
  }

  /** 创建 ALB 监控告警 */
  private createAlbAlarms(
    loadBalancer: elbv2.IApplicationLoadBalancer,
    targetGroup: elbv2.IApplicationTargetGroup,
    envName: EnvironmentName,
  ): void {
    /** ALB 告警使用即时触发 (单个数据点) */
    const ALB_ALARM_OVERRIDES = { evaluationPeriods: 1 } as const;

    // ALB UnHealthyHostCount 告警 — 有不健康实例
    this.createAlarm('UnhealthyHostAlarm', {
      alarmName: `${PROJECT_NAME}-${envName}-alb-unhealthy-hosts`,
      alarmDescription: 'ALB target group has unhealthy hosts',
      metric: targetGroup.metrics.unhealthyHostCount({
        period: METRIC_PERIOD,
        statistic: 'Maximum',
      }),
      threshold: 1,
      ...ALARM_DEFAULTS,
      ...ALB_ALARM_OVERRIDES,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
    });

    // ALB 5XX 错误告警 — 5 分钟内超过 10 个 5XX 响应
    this.createAlarm('Alb5xxAlarm', {
      alarmName: `${PROJECT_NAME}-${envName}-alb-5xx-high`,
      alarmDescription: 'ALB 5XX error count exceeds 10 per 5 minutes',
      metric: loadBalancer.metrics.httpCodeElb(elbv2.HttpCodeElb.ELB_5XX_COUNT, {
        period: METRIC_PERIOD,
        statistic: 'Sum',
      }),
      threshold: 10,
      ...ALARM_DEFAULTS,
      ...ALB_ALARM_OVERRIDES,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    });

    // ALB Target Response Time P95 告警 — 5 分钟内 P95 超过 500ms
    this.createAlarm('AlbLatencyP95Alarm', {
      alarmName: `${PROJECT_NAME}-${envName}-alb-latency-p95-high`,
      alarmDescription: 'ALB target response time P95 exceeds 500ms',
      metric: targetGroup.metrics.targetResponseTime({
        period: METRIC_PERIOD,
        statistic: 'p95',
      }),
      threshold: 0.5, // 500ms = 0.5 秒
      ...ALARM_DEFAULTS,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    });
  }

  /** 创建应用级错误日志告警 */
  private createApplicationErrorAlarm(logGroupName: string, envName: EnvironmentName): void {
    const logGroup = logs.LogGroup.fromLogGroupName(this, 'AppLogGroup', logGroupName);

    // 创建 Metric Filter — 过滤 JSON 日志中的 ERROR 级别
    // 注意: structlog JSONRenderer 输出的 JSON 格式带空格: "level": "error"
    const metricFilter = new logs.MetricFilter(this, 'ErrorLogFilter', {
      logGroup,
      filterPattern: logs.FilterPattern.literal('"level": "error"'),
      metricNamespace: `${PROJECT_NAME}/Application`,
      metricName: 'ErrorCount',
      metricValue: '1',
      defaultValue: 0,
    });

    // 基于 Metric Filter 创建告警
    this.createAlarm('AppErrorCountAlarm', {
      alarmName: `${PROJECT_NAME}-${envName}-app-error-count-high`,
      alarmDescription: 'Application ERROR log count exceeds 5 per 5 minutes',
      metric: metricFilter.metric({
        period: METRIC_PERIOD,
        statistic: 'Sum',
      }),
      threshold: 5,
      ...ALARM_DEFAULTS,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    });
  }

  /** 创建 CloudWatch Dashboard */
  private createDashboard(
    cluster: rds.IDatabaseCluster,
    service: ecs.FargateService,
    loadBalancer: elbv2.IApplicationLoadBalancer,
    targetGroup: elbv2.IApplicationTargetGroup,
    envName: EnvironmentName,
  ): void {
    const dashboard = new cloudwatch.Dashboard(this, 'Dashboard', {
      dashboardName: `${PROJECT_NAME}-${envName}`,
    });

    // Aurora 指标
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Aurora CPU Utilization',
        left: [cluster.metricCPUUtilization({ period: METRIC_PERIOD })],
        width: 8,
      }),
      new cloudwatch.GraphWidget({
        title: 'Aurora Freeable Memory',
        left: [cluster.metric('FreeableMemory', { period: METRIC_PERIOD })],
        width: 8,
      }),
      new cloudwatch.GraphWidget({
        title: 'Aurora Database Connections',
        left: [cluster.metric('DatabaseConnections', { period: METRIC_PERIOD })],
        width: 8,
      }),
    );

    // ECS 指标
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'ECS CPU Utilization',
        left: [service.metricCpuUtilization({ period: METRIC_PERIOD })],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'ECS Memory Utilization',
        left: [service.metricMemoryUtilization({ period: METRIC_PERIOD })],
        width: 12,
      }),
    );

    // ALB 指标
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'ALB Request Count',
        left: [loadBalancer.metrics.requestCount({ period: METRIC_PERIOD })],
        width: 8,
      }),
      new cloudwatch.GraphWidget({
        title: 'ALB 5XX Errors',
        left: [
          loadBalancer.metrics.httpCodeElb(elbv2.HttpCodeElb.ELB_5XX_COUNT, {
            period: METRIC_PERIOD,
          }),
        ],
        width: 8,
      }),
      new cloudwatch.GraphWidget({
        title: 'ALB Unhealthy Hosts',
        left: [targetGroup.metrics.unhealthyHostCount({ period: METRIC_PERIOD })],
        width: 8,
      }),
    );

    // API 响应延迟指标
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'ALB Target Response Time',
        left: [
          targetGroup.metrics.targetResponseTime({
            period: METRIC_PERIOD,
            statistic: 'Average',
          }),
          targetGroup.metrics.targetResponseTime({
            period: METRIC_PERIOD,
            statistic: 'p95',
          }),
        ],
        width: 12,
      }),
    );

    // Eval Pipeline 指标 (M13 — 自定义 CloudWatch Metric)
    dashboard.addWidgets(
      new cloudwatch.TextWidget({
        markdown: '## Eval Pipeline',
        width: 24,
        height: 1,
      }),
    );
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Eval Pipeline Job Succeeded',
        left: [
          new cloudwatch.Metric({
            namespace: 'EvalPipeline',
            metricName: 'JobSucceeded',
            period: METRIC_PERIOD,
            statistic: 'Sum',
          }),
        ],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'Eval Pipeline Job Failed',
        left: [
          new cloudwatch.Metric({
            namespace: 'EvalPipeline',
            metricName: 'JobFailed',
            period: METRIC_PERIOD,
            statistic: 'Sum',
          }),
        ],
        width: 12,
      }),
    );

    // SSE 并发连接指标 (C-S5-3 — Builder + Execution SSE 隔离监控)
    dashboard.addWidgets(
      new cloudwatch.TextWidget({
        markdown: '## SSE Connections',
        width: 24,
        height: 1,
      }),
    );
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'SSE Active Connections',
        left: [
          new cloudwatch.Metric({
            namespace: 'SSEConnections',
            metricName: 'ActiveConnections',
            period: METRIC_PERIOD,
            statistic: 'Maximum',
          }),
        ],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'SSE Active Users',
        left: [
          new cloudwatch.Metric({
            namespace: 'SSEConnections',
            metricName: 'ActiveUsers',
            period: METRIC_PERIOD,
            statistic: 'Maximum',
          }),
        ],
        width: 12,
      }),
    );
  }

  /** 创建 ECS 部署失败 EventBridge 规则 */
  private createDeploymentFailureRule(envName: EnvironmentName): void {
    new events.Rule(this, 'EcsDeployFailureRule', {
      ruleName: `${PROJECT_NAME}-${envName}-ecs-deploy-failure`,
      description: 'ECS 服务部署失败时发送 SNS 告警通知',
      eventPattern: {
        source: ['aws.ecs'],
        detailType: ['ECS Deployment State Change'],
        detail: {
          eventType: ['ERROR'],
        },
      },
      targets: [
        new events_targets.SnsTopic(this.alertTopic, {
          message: events.RuleTargetInput.fromText(
            `🚨 ECS 部署失败 [${envName}]\n` +
              `原因: ${events.EventField.fromPath('$.detail.reason')}`,
          ),
        }),
      ],
    });
  }

  /** CDK Nag 合规规则抑制 */
  private suppressNagRules(hasEncryptionKey: boolean): void {
    const suppressions: Array<{ id: string; reason: string }> = [
      // SNS Topic: HTTPS 发布强制策略 — 告警通知为内部 CloudWatch Alarm 使用
      {
        id: 'AwsSolutions-SNS3',
        reason:
          'Alert topic is for internal CloudWatch alarm notifications only; SSL enforcement for publishing will be added when external subscribers are introduced',
      },
    ];

    // SNS Topic: 未提供 encryptionKey 时抑制 KMS 加密规则
    if (!hasEncryptionKey) {
      suppressions.push({
        id: 'AwsSolutions-SNS2',
        reason:
          'SNS Topic KMS encryption is configured when encryptionKey is provided via MonitoringStackProps; alert notifications do not contain sensitive data',
      });
    }

    NagSuppressions.addResourceSuppressions(this.alertTopic, suppressions);
  }
}

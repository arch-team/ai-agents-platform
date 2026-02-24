import * as cdk from 'aws-cdk-lib';
import * as budgets from 'aws-cdk-lib/aws-budgets';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import { PROJECT_NAME, type BaseStackProps } from '../config';

export interface BillingStackProps extends BaseStackProps {
  /** 告警通知邮箱 @default undefined (不创建邮件订阅) */
  readonly alertEmail?: string;
}

/**
 * BillingStack - AWS 成本预算和告警栈。
 * @remarks
 * 创建月度预算告警,并在达到指定阈值时发送通知。Dev: $100/月, Prod: $1000/月。
 */
export class BillingStack extends cdk.Stack {
  /** AWS Budget 资源 */
  public readonly budget: budgets.CfnBudget;

  constructor(scope: Construct, id: string, props: BillingStackProps) {
    super(scope, id, props);

    const { alertEmail, envName } = props;

    // 根据环境设置预算限额
    const budgetLimit = envName === 'prod' ? 1000 : 100;

    // 构建告警订阅配置
    const subscribers: budgets.CfnBudget.SubscriberProperty[] = alertEmail
      ? [{ address: alertEmail, subscriptionType: 'EMAIL' }]
      : [];

    // 创建月度预算告警
    this.budget = new budgets.CfnBudget(this, 'MonthlyBudget', {
      budget: {
        budgetName: `${PROJECT_NAME}-${envName}-monthly-budget`,
        budgetType: 'COST',
        timeUnit: 'MONTHLY',
        budgetLimit: {
          amount: budgetLimit,
          unit: 'USD',
        },
      },
      notificationsWithSubscribers: [
        // 80% 实际成本告警
        {
          notification: {
            notificationType: 'ACTUAL',
            comparisonOperator: 'GREATER_THAN',
            threshold: 80,
            thresholdType: 'PERCENTAGE',
          },
          subscribers,
        },
        // 100% 实际成本告警
        {
          notification: {
            notificationType: 'ACTUAL',
            comparisonOperator: 'GREATER_THAN',
            threshold: 100,
            thresholdType: 'PERCENTAGE',
          },
          subscribers,
        },
        // 120% 预测成本告警
        {
          notification: {
            notificationType: 'FORECASTED',
            comparisonOperator: 'GREATER_THAN',
            threshold: 120,
            thresholdType: 'PERCENTAGE',
          },
          subscribers,
        },
      ],
    });

    // CDK Nag 抑制
    this.suppressNagRules();
  }

  /** CDK Nag 合规规则抑制 */
  private suppressNagRules(): void {
    // AWS Budgets 为 L1 Construct (CfnBudget)，无 L2 高级抽象，因此某些 CDK Nag 规则可能误报
    // 如果后续 synth 时发现 Nag 报错，在此处添加 suppressions
    NagSuppressions.addResourceSuppressions(
      this.budget,
      [
        {
          id: 'AwsSolutions-BGT1',
          reason:
            'Budget notifications are configured with email subscribers; SNS topic is not required for basic email alerts',
        },
      ],
      true,
    );
  }
}

import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { BillingStack } from '../../lib/stacks/billing-stack';

describe('BillingStack', () => {
  let app: cdk.App;

  beforeEach(() => {
    app = new cdk.App();
  });

  describe('Dev Environment', () => {
    let template: Template;

    beforeEach(() => {
      const stack = new BillingStack(app, 'TestBillingStack', {
        env: { account: '123456789012', region: 'ap-northeast-1' },
        envName: 'dev',
        alertEmail: 'test@example.com',
      });
      template = Template.fromStack(stack);
    });

    it('应创建 CfnBudget 资源', () => {
      template.resourceCountIs('AWS::Budgets::Budget', 1);
    });

    it('Dev 环境预算金额应为 $100', () => {
      template.hasResourceProperties('AWS::Budgets::Budget', {
        Budget: Match.objectLike({
          BudgetLimit: {
            Amount: 100,
            Unit: 'USD',
          },
          BudgetType: 'COST',
          TimeUnit: 'MONTHLY',
        }),
      });
    });

    it('应包含 80% 实际成本告警', () => {
      template.hasResourceProperties('AWS::Budgets::Budget', {
        NotificationsWithSubscribers: Match.arrayWith([
          Match.objectLike({
            Notification: {
              NotificationType: 'ACTUAL',
              ComparisonOperator: 'GREATER_THAN',
              Threshold: 80,
              ThresholdType: 'PERCENTAGE',
            },
          }),
        ]),
      });
    });

    it('应包含 100% 实际成本告警', () => {
      template.hasResourceProperties('AWS::Budgets::Budget', {
        NotificationsWithSubscribers: Match.arrayWith([
          Match.objectLike({
            Notification: {
              NotificationType: 'ACTUAL',
              ComparisonOperator: 'GREATER_THAN',
              Threshold: 100,
              ThresholdType: 'PERCENTAGE',
            },
          }),
        ]),
      });
    });

    it('应包含 120% 预测成本告警', () => {
      template.hasResourceProperties('AWS::Budgets::Budget', {
        NotificationsWithSubscribers: Match.arrayWith([
          Match.objectLike({
            Notification: {
              NotificationType: 'FORECASTED',
              ComparisonOperator: 'GREATER_THAN',
              Threshold: 120,
              ThresholdType: 'PERCENTAGE',
            },
          }),
        ]),
      });
    });

    it('应配置邮件订阅', () => {
      template.hasResourceProperties('AWS::Budgets::Budget', {
        NotificationsWithSubscribers: Match.arrayWith([
          Match.objectLike({
            Subscribers: [
              {
                Address: 'test@example.com',
                SubscriptionType: 'EMAIL',
              },
            ],
          }),
        ]),
      });
    });
  });

  describe('Prod Environment', () => {
    let template: Template;

    beforeEach(() => {
      const stack = new BillingStack(app, 'TestBillingStack', {
        env: { account: '123456789012', region: 'ap-northeast-1' },
        envName: 'prod',
        alertEmail: 'prod@example.com',
      });
      template = Template.fromStack(stack);
    });

    it('Prod 环境预算金额应为 $1000', () => {
      template.hasResourceProperties('AWS::Budgets::Budget', {
        Budget: Match.objectLike({
          BudgetLimit: {
            Amount: 1000,
            Unit: 'USD',
          },
        }),
      });
    });
  });

  describe('Without Email', () => {
    let template: Template;

    beforeEach(() => {
      const stack = new BillingStack(app, 'TestBillingStack', {
        env: { account: '123456789012', region: 'ap-northeast-1' },
        envName: 'dev',
        // alertEmail 未提供
      });
      template = Template.fromStack(stack);
    });

    it('未提供邮箱时不创建通知配置', () => {
      template.hasResourceProperties('AWS::Budgets::Budget', {
        NotificationsWithSubscribers: Match.absent(),
      });
    });
  });
});

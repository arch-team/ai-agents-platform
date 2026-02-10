import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { KmsConstruct } from './kms.construct';

describe('KmsConstruct', () => {
  let template: Template;

  describe('默认配置', () => {
    beforeEach(() => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      new KmsConstruct(stack, 'TestKms', { envName: 'prod' });
      template = Template.fromStack(stack);
    });

    it('应创建 KMS Key', () => {
      template.resourceCountIs('AWS::KMS::Key', 1);
    });

    it('应默认启用密钥轮换', () => {
      template.hasResourceProperties('AWS::KMS::Key', {
        EnableKeyRotation: true,
      });
    });

    it('应设置描述信息', () => {
      template.hasResourceProperties('AWS::KMS::Key', {
        Description: 'AI Agents Platform 数据加密主密钥',
      });
    });

    it('应创建默认别名', () => {
      template.hasResourceProperties('AWS::KMS::Alias', {
        AliasName: 'alias/ai-agents-platform',
      });
    });

    it('应设置 RemovalPolicy 为 RETAIN', () => {
      template.hasResource('AWS::KMS::Key', {
        DeletionPolicy: 'Retain',
        UpdateReplacePolicy: 'Retain',
      });
    });
  });

  describe('环境区分', () => {
    it('Dev 环境应设置 RemovalPolicy 为 DESTROY', () => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      new KmsConstruct(stack, 'TestKms', { envName: 'dev' });
      const devTemplate = Template.fromStack(stack);

      devTemplate.hasResource('AWS::KMS::Key', {
        DeletionPolicy: 'Delete',
        UpdateReplacePolicy: 'Delete',
      });
    });
  });

  describe('自定义配置', () => {
    it('应支持自定义别名', () => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      new KmsConstruct(stack, 'TestKms', {
        envName: 'prod',
        alias: 'custom-key-alias',
      });
      template = Template.fromStack(stack);

      template.hasResourceProperties('AWS::KMS::Alias', {
        AliasName: 'alias/custom-key-alias',
      });
    });

    it('应支持禁用密钥轮换', () => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      new KmsConstruct(stack, 'TestKms', {
        envName: 'prod',
        enableKeyRotation: false,
      });
      template = Template.fromStack(stack);

      template.hasResourceProperties('AWS::KMS::Key', {
        EnableKeyRotation: false,
      });
    });
  });

  describe('公开属性', () => {
    it('应暴露 key 属性', () => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const construct = new KmsConstruct(stack, 'TestKms', { envName: 'dev' });

      expect(construct.key).toBeDefined();
    });
  });
});

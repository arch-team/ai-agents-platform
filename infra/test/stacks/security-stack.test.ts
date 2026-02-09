import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Template } from 'aws-cdk-lib/assertions';
import { SecurityStack } from '../../lib/stacks/security-stack';

describe('SecurityStack', () => {
  let template: Template;

  describe('基本配置 (dev 环境)', () => {
    beforeEach(() => {
      const app = new cdk.App();
      const vpcStack = new cdk.Stack(app, 'VpcStack');
      const vpc = new ec2.Vpc(vpcStack, 'TestVpc');

      const stack = new SecurityStack(app, 'TestSecurityStack', {
        vpc,
        envName: 'dev',
      });
      template = Template.fromStack(stack);
    });

    it('应创建 KMS Key', () => {
      template.hasResourceProperties('AWS::KMS::Key', {
        EnableKeyRotation: true,
      });
    });

    it('应创建带环境后缀的 KMS 别名', () => {
      template.hasResourceProperties('AWS::KMS::Alias', {
        AliasName: 'alias/ai-agents-platform-dev',
      });
    });

    it('应创建两个安全组', () => {
      template.resourceCountIs('AWS::EC2::SecurityGroup', 2);
    });

    it('应输出 EncryptionKeyArn', () => {
      template.hasOutput('EncryptionKeyArn', {
        Description: 'KMS 加密密钥 ARN',
      });
    });

    it('dev 环境不应创建 VPC Endpoint', () => {
      template.resourceCountIs('AWS::EC2::VPCEndpoint', 0);
    });
  });

  describe('Prod 环境', () => {
    it('应创建 Secrets Manager VPC Endpoint', () => {
      const app = new cdk.App();
      const vpcStack = new cdk.Stack(app, 'VpcStack');
      const vpc = new ec2.Vpc(vpcStack, 'TestVpc');

      const stack = new SecurityStack(app, 'TestSecurityStack', {
        vpc,
        envName: 'prod',
      });
      const prodTemplate = Template.fromStack(stack);

      // InterfaceVpcEndpoint 创建在 SecurityStack 中
      prodTemplate.resourceCountIs('AWS::EC2::VPCEndpoint', 1);
    });
  });

  describe('公开属性', () => {
    it('应暴露 encryptionKey, apiSecurityGroup, dbSecurityGroup', () => {
      const app = new cdk.App();
      const vpcStack = new cdk.Stack(app, 'VpcStack');
      const vpc = new ec2.Vpc(vpcStack, 'TestVpc');

      const stack = new SecurityStack(app, 'TestSecurityStack', {
        vpc,
        envName: 'dev',
      });

      expect(stack.encryptionKey).toBeDefined();
      expect(stack.apiSecurityGroup).toBeDefined();
      expect(stack.dbSecurityGroup).toBeDefined();
    });
  });
});

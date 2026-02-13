import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { SecurityStack } from '../../lib/stacks/security-stack';
import { createVpcDependency } from '../helpers/test-utils';

describe('SecurityStack', () => {
  let template: Template;
  let stack: SecurityStack;

  describe('Dev 环境', () => {
    beforeEach(() => {
      const app = new cdk.App();
      const vpc = createVpcDependency(app);

      stack = new SecurityStack(app, 'TestSecurityStack', {
        vpc,
        envName: 'dev',
      });
      template = Template.fromStack(stack);
    });

    it('应创建 KMS Key (启用密钥轮换)', () => {
      template.hasResourceProperties('AWS::KMS::Key', {
        EnableKeyRotation: true,
      });
    });

    it('应创建带环境后缀的 KMS 别名', () => {
      template.hasResourceProperties('AWS::KMS::Alias', {
        AliasName: 'alias/ai-agents-platform-dev',
      });
    });

    it('应创建两个安全组 (API + DB)', () => {
      template.resourceCountIs('AWS::EC2::SecurityGroup', 2);
    });

    it('应创建 JWT Secret (Secrets Manager)', () => {
      template.hasResourceProperties('AWS::SecretsManager::Secret', {
        Name: 'dev/ai-platform/jwt-secret',
        Description: 'JWT 签名密钥 — 用于 API 认证 Token 签发和验证',
        GenerateSecretString: {
          GenerateStringKey: 'secret_key',
          PasswordLength: 64,
          ExcludePunctuation: true,
        },
      });
    });

    it('Dev 环境不应创建 VPC Endpoint', () => {
      template.resourceCountIs('AWS::EC2::VPCEndpoint', 0);
    });

    it('应输出 EncryptionKeyArn', () => {
      template.hasOutput('EncryptionKeyArn', {
        Description: 'KMS encryption key ARN',
      });
    });

    it('应输出 JwtSecretArn', () => {
      template.hasOutput('JwtSecretArn', {
        Description: 'JWT signing secret ARN',
      });
    });
  });

  describe('Prod 环境', () => {
    it('应创建 Secrets Manager VPC Endpoint', () => {
      const app = new cdk.App();
      const vpc = createVpcDependency(app);

      const prodStack = new SecurityStack(app, 'ProdSecurityStack', {
        vpc,
        envName: 'prod',
      });
      const prodTemplate = Template.fromStack(prodStack);

      prodTemplate.resourceCountIs('AWS::EC2::VPCEndpoint', 1);
    });
  });

  describe('公开属性', () => {
    it('应暴露 encryptionKey, apiSecurityGroup, dbSecurityGroup, jwtSecret', () => {
      const app = new cdk.App();
      const vpc = createVpcDependency(app);

      const attrStack = new SecurityStack(app, 'AttrSecurityStack', {
        vpc,
        envName: 'dev',
      });

      expect(attrStack.encryptionKey).toBeDefined();
      expect(attrStack.apiSecurityGroup).toBeDefined();
      expect(attrStack.dbSecurityGroup).toBeDefined();
      expect(attrStack.jwtSecret).toBeDefined();
    });
  });
});

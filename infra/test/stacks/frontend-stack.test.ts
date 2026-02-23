import * as cdk from 'aws-cdk-lib';
import { Match, Template } from 'aws-cdk-lib/assertions';
import { FrontendStack } from '../../lib/stacks/frontend-stack';
import { TEST_ENV } from '../helpers/test-utils';

describe('FrontendStack', () => {
  let template: Template;
  let stack: FrontendStack;

  describe('Dev 环境', () => {
    beforeEach(() => {
      const app = new cdk.App();
      stack = new FrontendStack(app, 'TestFrontendStack', {
        env: TEST_ENV,
        envName: 'dev',
      });
      template = Template.fromStack(stack);
    });

    it('应创建私有 S3 Bucket（含正确 Bucket 名）', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        BucketName: 'ai-agents-platform-frontend-dev-897473',
        BucketEncryption: Match.objectLike({
          ServerSideEncryptionConfiguration: Match.anyValue(),
        }),
      });
    });

    it('S3 Bucket 应阻止所有公开访问', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        PublicAccessBlockConfiguration: {
          BlockPublicAcls: true,
          BlockPublicPolicy: true,
          IgnorePublicAcls: true,
          RestrictPublicBuckets: true,
        },
      });
    });

    it('S3 Bucket 应强制 SSL', () => {
      template.hasResourceProperties('AWS::S3::BucketPolicy', {
        PolicyDocument: Match.objectLike({
          Statement: Match.arrayWith([
            Match.objectLike({
              Condition: Match.objectLike({
                Bool: { 'aws:SecureTransport': 'false' },
              }),
              Effect: 'Deny',
            }),
          ]),
        }),
      });
    });

    it('应创建 CloudFront 分发', () => {
      template.resourceCountIs('AWS::CloudFront::Distribution', 1);
    });

    it('应配置 SPA 错误响应（404/403 → index.html）', () => {
      template.hasResourceProperties('AWS::CloudFront::Distribution', {
        DistributionConfig: Match.objectLike({
          CustomErrorResponses: Match.arrayWith([
            Match.objectLike({
              ErrorCode: 404,
              ResponseCode: 200,
              ResponsePagePath: '/index.html',
            }),
            Match.objectLike({
              ErrorCode: 403,
              ResponseCode: 200,
              ResponsePagePath: '/index.html',
            }),
          ]),
        }),
      });
    });

    it('Dev 环境应使用 PRICE_CLASS_100', () => {
      template.hasResourceProperties('AWS::CloudFront::Distribution', {
        DistributionConfig: Match.objectLike({
          PriceClass: 'PriceClass_100',
        }),
      });
    });

    it('应将默认根对象设置为 index.html', () => {
      template.hasResourceProperties('AWS::CloudFront::Distribution', {
        DistributionConfig: Match.objectLike({
          DefaultRootObject: 'index.html',
        }),
      });
    });

    it('应将 HTTP 重定向到 HTTPS', () => {
      template.hasResourceProperties('AWS::CloudFront::Distribution', {
        DistributionConfig: Match.objectLike({
          DefaultCacheBehavior: Match.objectLike({
            ViewerProtocolPolicy: 'redirect-to-https',
          }),
        }),
      });
    });

    it('应输出 FrontendUrl', () => {
      template.hasOutput('FrontendUrl', {
        Description: 'Frontend CloudFront URL (dev)',
      });
    });

    it('应输出 FrontendBucketName', () => {
      template.hasOutput('FrontendBucketName', {
        Description: 'Frontend S3 bucket name (dev)',
      });
    });

    it('应暴露 bucket、distribution 和 distributionUrl 公开属性', () => {
      expect(stack.bucket).toBeDefined();
      expect(stack.distribution).toBeDefined();
      expect(stack.distributionUrl).toMatch(/^https:\/\//);
    });
  });

  describe('Prod 环境', () => {
    it('应使用 PRICE_CLASS_ALL', () => {
      const app = new cdk.App();
      const prodStack = new FrontendStack(app, 'ProdFrontendStack', {
        env: TEST_ENV,
        envName: 'prod',
      });
      const prodTemplate = Template.fromStack(prodStack);

      prodTemplate.hasResourceProperties('AWS::CloudFront::Distribution', {
        DistributionConfig: Match.objectLike({
          PriceClass: 'PriceClass_All',
        }),
      });
    });

    it('Prod 环境 Bucket 应使用 RETAIN RemovalPolicy', () => {
      const app = new cdk.App();
      const prodStack = new FrontendStack(app, 'ProdFrontendStack2', {
        env: TEST_ENV,
        envName: 'prod',
      });
      const prodTemplate = Template.fromStack(prodStack);

      // RETAIN 策略下不应有 AutoDeleteObjects 的自定义资源 Lambda
      // S3 Bucket 应存在（DeletionPolicy 为 Retain）
      prodTemplate.hasResource('AWS::S3::Bucket', {
        DeletionPolicy: 'Retain',
      });
    });
  });
});

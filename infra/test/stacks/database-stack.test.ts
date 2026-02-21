import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { DatabaseStack } from '../../lib/stacks/database-stack';
import { createCrossStackDbDependencies } from '../helpers/test-utils';

describe('DatabaseStack', () => {
  describe('Dev 环境', () => {
    let template: Template;
    let stack: DatabaseStack;

    beforeEach(() => {
      const app = new cdk.App();
      const { vpc, dbSecurityGroup, encryptionKey } = createCrossStackDbDependencies(app);

      stack = new DatabaseStack(app, 'TestDatabaseStack', {
        vpc,
        dbSecurityGroup,
        encryptionKey,
        envName: 'dev',
      });
      template = Template.fromStack(stack);
    });

    it('应创建 Aurora MySQL 集群', () => {
      template.hasResourceProperties('AWS::RDS::DBCluster', {
        Engine: 'aurora-mysql',
      });
    });

    it('凭证 Secret 名称应正确', () => {
      template.hasResourceProperties('AWS::SecretsManager::Secret', {
        Name: 'dev/ai-agents-platform/db-credentials',
      });
    });

    it('Dev 环境不应启用 Performance Insights', () => {
      template.hasResourceProperties('AWS::RDS::DBInstance', {
        EnablePerformanceInsights: false,
      });
    });

    describe('Outputs', () => {
      it('应输出 ClusterEndpoint', () => {
        template.hasOutput('ClusterEndpoint', {
          Description: 'Aurora cluster endpoint',
        });
      });

      it('应输出 SecretArn', () => {
        template.hasOutput('SecretArn', {
          Description: 'Database credentials Secret ARN',
        });
      });

      it('应输出 KnowledgeBucketName', () => {
        template.hasOutput('KnowledgeBucketName', {
          Description: 'Knowledge documents S3 bucket name',
        });
      });
    });

    describe('公开属性', () => {
      it('应暴露 cluster、dbSecret 和 knowledgeBucket', () => {
        expect(stack.cluster).toBeDefined();
        expect(stack.dbSecret).toBeDefined();
        expect(stack.knowledgeBucket).toBeDefined();
      });
    });
  });

  describe('Prod 环境', () => {
    let template: Template;

    beforeEach(() => {
      const app = new cdk.App();
      const { vpc, dbSecurityGroup, encryptionKey } = createCrossStackDbDependencies(app);

      const stack = new DatabaseStack(app, 'TestDatabaseStack', {
        vpc,
        dbSecurityGroup,
        encryptionKey,
        envName: 'prod',
      });
      template = Template.fromStack(stack);
    });

    it('Prod 环境应启用 Performance Insights', () => {
      const instances = template.findResources('AWS::RDS::DBInstance');
      const instanceIds = Object.keys(instances);
      expect(instanceIds.length).toBeGreaterThanOrEqual(1);

      for (const id of instanceIds) {
        expect(instances[id].Properties.EnablePerformanceInsights).toBe(true);
      }
    });
  });

  describe('S3 知识库 Bucket', () => {
    let template: Template;

    beforeEach(() => {
      const app = new cdk.App();
      const { vpc, dbSecurityGroup, encryptionKey } = createCrossStackDbDependencies(app);

      const stack = new DatabaseStack(app, 'TestDatabaseStack', {
        vpc,
        dbSecurityGroup,
        encryptionKey,
        envName: 'dev',
      });
      template = Template.fromStack(stack);
    });

    it('应创建 S3 Bucket', () => {
      template.resourceCountIs('AWS::S3::Bucket', 1);
    });

    it('应启用版本控制', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        VersioningConfiguration: { Status: 'Enabled' },
      });
    });

    it('应阻止公开访问', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        PublicAccessBlockConfiguration: {
          BlockPublicAcls: true,
          BlockPublicPolicy: true,
          IgnorePublicAcls: true,
          RestrictPublicBuckets: true,
        },
      });
    });

    it('应配置生命周期规则 — 旧版本 30 天过期', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        LifecycleConfiguration: {
          Rules: Match.arrayWith([
            Match.objectLike({
              NoncurrentVersionExpiration: { NoncurrentDays: 30 },
              Status: 'Enabled',
            }),
          ]),
        },
      });
    });

    it('应配置生命周期规则 — 未完成分段上传 7 天清理', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        LifecycleConfiguration: {
          Rules: Match.arrayWith([
            Match.objectLike({
              AbortIncompleteMultipartUpload: { DaysAfterInitiation: 7 },
              Status: 'Enabled',
            }),
          ]),
        },
      });
    });

    it('Bucket 名称应包含环境后缀', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        BucketName: 'ai-agents-platform-knowledge-dev',
      });
    });
  });
});

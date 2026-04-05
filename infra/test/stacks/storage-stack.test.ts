import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { StorageStack } from '../../lib/stacks/storage-stack';
import { createVpcDependency } from '../helpers/test-utils';

describe('StorageStack', () => {
  let template: Template;
  let stack: StorageStack;

  beforeEach(() => {
    const app = new cdk.App();
    const vpc = createVpcDependency(app);

    stack = new StorageStack(app, 'TestStorageStack', {
      vpc,
      envName: 'dev',
    });
    template = Template.fromStack(stack);
  });

  describe('S3 Workspace Bucket', () => {
    it('应创建 Workspace S3 存储桶', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        BucketName: 'ai-agents-platform-workspaces-dev',
      });
    });

    it('应启用 S3 托管加密', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        BucketEncryption: {
          ServerSideEncryptionConfiguration: [
            {
              ServerSideEncryptionByDefault: {
                SSEAlgorithm: 'AES256',
              },
            },
          ],
        },
      });
    });

    it('应阻止所有公开访问', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        PublicAccessBlockConfiguration: {
          BlockPublicAcls: true,
          BlockPublicPolicy: true,
          IgnorePublicAcls: true,
          RestrictPublicBuckets: true,
        },
      });
    });

    it('应配置生命周期规则 — 90 天后迁移到 IA', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        LifecycleConfiguration: {
          Rules: Match.arrayWith([
            Match.objectLike({
              Status: 'Enabled',
              Transitions: Match.arrayWith([
                Match.objectLike({
                  StorageClass: 'STANDARD_IA',
                  TransitionInDays: 90,
                }),
              ]),
            }),
          ]),
        },
      });
    });

    it('应强制 SSL 传输 (BucketPolicy)', () => {
      template.hasResourceProperties('AWS::S3::BucketPolicy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Effect: 'Deny',
              Condition: {
                Bool: { 'aws:SecureTransport': 'false' },
              },
            }),
          ]),
        },
      });
    });

    it('Dev 环境应使用 DESTROY 删除策略', () => {
      const resources = template.findResources('AWS::S3::Bucket');
      const bucketKey = Object.keys(resources).find((k) =>
        JSON.stringify(resources[k]).includes('workspaces'),
      );
      expect(bucketKey).toBeDefined();
      expect(resources[bucketKey!].UpdateReplacePolicy).toBe('Delete');
      expect(resources[bucketKey!].DeletionPolicy).toBe('Delete');
    });
  });

  describe('EFS FileSystem', () => {
    it('应创建 EFS 文件系统', () => {
      template.hasResourceProperties('AWS::EFS::FileSystem', {
        Encrypted: true,
      });
    });

    it('应配置性能模式 (Dev: Bursting)', () => {
      template.hasResourceProperties('AWS::EFS::FileSystem', {
        ThroughputMode: 'bursting',
      });
    });

    it('应在 Private 子网中创建挂载目标', () => {
      template.resourceCountIs('AWS::EFS::MountTarget', 2);
    });

    it('应创建 EFS 安全组并允许 NFS 端口', () => {
      template.hasResourceProperties('AWS::EC2::SecurityGroup', {
        GroupDescription: Match.stringLikeRegexp('EFS.*security group'),
      });
    });
  });

  describe('Outputs', () => {
    it('应输出 WorkspaceBucketName', () => {
      template.hasOutput('WorkspaceBucketName', {
        Description: Match.stringLikeRegexp('Workspace'),
      });
    });

    it('应输出 WorkspaceBucketArn', () => {
      template.hasOutput('WorkspaceBucketArn', {
        Description: Match.stringLikeRegexp('Workspace.*ARN'),
      });
    });

    it('应输出 SkillLibraryEfsId', () => {
      template.hasOutput('SkillLibraryEfsId', {
        Description: Match.stringLikeRegexp('Skill Library.*EFS'),
      });
    });
  });

  describe('公开属性', () => {
    it('应暴露 workspaceBucket, skillLibraryFs, efsSecurityGroup', () => {
      expect(stack.workspaceBucket).toBeDefined();
      expect(stack.skillLibraryFs).toBeDefined();
      expect(stack.efsSecurityGroup).toBeDefined();
    });
  });

  describe('Prod 环境配置', () => {
    it('Prod 环境 S3 Bucket 应使用 RETAIN 删除策略', () => {
      const app = new cdk.App();
      const vpc = createVpcDependency(app);

      const prodStack = new StorageStack(app, 'ProdStorageStack', {
        vpc,
        envName: 'prod',
      });
      const prodTemplate = Template.fromStack(prodStack);

      const resources = prodTemplate.findResources('AWS::S3::Bucket');
      const bucketKey = Object.keys(resources).find((k) =>
        JSON.stringify(resources[k]).includes('workspaces'),
      );
      expect(bucketKey).toBeDefined();
      expect(resources[bucketKey!].UpdateReplacePolicy).toBe('Retain');
      expect(resources[bucketKey!].DeletionPolicy).toBe('Retain');
    });

    it('Prod 环境 EFS 应使用 RETAIN 删除策略', () => {
      const app = new cdk.App();
      const vpc = createVpcDependency(app);

      const prodStack = new StorageStack(app, 'ProdStorageStack2', {
        vpc,
        envName: 'prod',
      });
      const prodTemplate = Template.fromStack(prodStack);

      const resources = prodTemplate.findResources('AWS::EFS::FileSystem');
      const efsKey = Object.keys(resources)[0];
      expect(resources[efsKey].UpdateReplacePolicy).toBe('Retain');
      expect(resources[efsKey].DeletionPolicy).toBe('Retain');
    });
  });
});

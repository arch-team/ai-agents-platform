import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { DatabaseStack } from '../../lib/stacks/database-stack';
import { createCrossStackDbDependencies } from '../helpers/test-utils';

describe('DatabaseStack', () => {
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

  it('应创建 Aurora 集群', () => {
    template.hasResourceProperties('AWS::RDS::DBCluster', {
      Engine: 'aurora-mysql',
    });
  });

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

  it('凭证 Secret 名称应正确', () => {
    template.hasResourceProperties('AWS::SecretsManager::Secret', {
      Name: 'dev/ai-agents-platform/db-credentials',
    });
  });

  describe('公开属性', () => {
    it('应暴露 cluster 和 dbSecret', () => {
      expect(stack.cluster).toBeDefined();
      expect(stack.dbSecret).toBeDefined();
    });
  });
});

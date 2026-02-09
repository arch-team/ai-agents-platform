import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import { Template } from 'aws-cdk-lib/assertions';
import { DatabaseStack } from '../../lib/stacks/database-stack';

// 辅助函数: 创建含 Isolated 子网的 VPC
function createTestVpc(stack: cdk.Stack) {
  return new ec2.Vpc(stack, 'TestVpc', {
    subnetConfiguration: [
      { name: 'Public', subnetType: ec2.SubnetType.PUBLIC, cidrMask: 24 },
      { name: 'Private', subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS, cidrMask: 24 },
      { name: 'Isolated', subnetType: ec2.SubnetType.PRIVATE_ISOLATED, cidrMask: 24 },
    ],
  });
}

describe('DatabaseStack', () => {
  let template: Template;
  let stack: DatabaseStack;

  beforeEach(() => {
    const app = new cdk.App();
    const vpcStack = new cdk.Stack(app, 'VpcStack');
    const vpc = createTestVpc(vpcStack);
    const dbSecurityGroup = new ec2.SecurityGroup(vpcStack, 'TestDbSg', { vpc });
    const encryptionKey = new kms.Key(vpcStack, 'TestKey');

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
      Description: 'Aurora 集群端点',
    });
  });

  it('应输出 SecretArn', () => {
    template.hasOutput('SecretArn', {
      Description: '数据库凭证 Secret ARN',
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

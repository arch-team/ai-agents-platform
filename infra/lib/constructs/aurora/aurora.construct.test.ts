import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { AuroraConstruct } from './aurora.construct';

describe('AuroraConstruct', () => {
  // 辅助函数: 创建测试用 VPC (含 Isolated 子网) 和安全组
  function createTestDependencies(stack: cdk.Stack) {
    const vpc = new ec2.Vpc(stack, 'TestVpc', {
      subnetConfiguration: [
        { name: 'Public', subnetType: ec2.SubnetType.PUBLIC, cidrMask: 24 },
        { name: 'Private', subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS, cidrMask: 24 },
        { name: 'Isolated', subnetType: ec2.SubnetType.PRIVATE_ISOLATED, cidrMask: 24 },
      ],
    });
    const securityGroup = new ec2.SecurityGroup(stack, 'TestSg', { vpc });
    const encryptionKey = new kms.Key(stack, 'TestKey');
    return { vpc, securityGroup, encryptionKey };
  }

  describe('Dev 环境', () => {
    let template: Template;

    beforeEach(() => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const { vpc, securityGroup, encryptionKey } = createTestDependencies(stack);

      new AuroraConstruct(stack, 'TestAurora', {
        vpc,
        securityGroup,
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

    it('应使用 Aurora MySQL 3.x 引擎版本', () => {
      template.hasResourceProperties('AWS::RDS::DBCluster', {
        EngineVersion: Match.stringLikeRegexp('aurora\\.3\\.'),
      });
    });

    it('应使用 PRIVATE_ISOLATED 子网', () => {
      template.hasResourceProperties('AWS::RDS::DBCluster', {
        DBSubnetGroupName: Match.anyValue(),
      });
    });

    it('应启用存储加密', () => {
      template.hasResourceProperties('AWS::RDS::DBCluster', {
        StorageEncrypted: true,
      });
    });

    it('Dev 环境不应启用删除保护', () => {
      template.hasResourceProperties('AWS::RDS::DBCluster', {
        DeletionProtection: false,
      });
    });

    it('应创建 Secrets Manager 凭证', () => {
      template.hasResourceProperties('AWS::SecretsManager::Secret', {
        Name: 'dev/ai-agents-platform/db-credentials',
      });
    });

    it('应存在 Writer 实例', () => {
      template.hasResourceProperties('AWS::RDS::DBInstance', {
        Engine: 'aurora-mysql',
        PubliclyAccessible: false,
      });
    });

    it('Dev 环境只有 Writer，没有 Reader', () => {
      template.resourceCountIs('AWS::RDS::DBInstance', 1);
    });

    it('应启用 CloudWatch 日志导出 (error, slowquery)', () => {
      template.hasResourceProperties('AWS::RDS::DBCluster', {
        EnableCloudwatchLogsExports: Match.arrayWith(['error', 'slowquery']),
      });
    });

    it('应启用 IAM 认证', () => {
      template.hasResourceProperties('AWS::RDS::DBCluster', {
        EnableIAMDatabaseAuthentication: true,
      });
    });

    it('Dev 环境备份保留 7 天', () => {
      template.hasResourceProperties('AWS::RDS::DBCluster', {
        BackupRetentionPeriod: 7,
      });
    });
  });

  describe('Prod 环境', () => {
    let template: Template;

    beforeEach(() => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const { vpc, securityGroup, encryptionKey } = createTestDependencies(stack);

      new AuroraConstruct(stack, 'TestAurora', {
        vpc,
        securityGroup,
        encryptionKey,
        envName: 'prod',
      });
      template = Template.fromStack(stack);
    });

    it('Prod 环境应启用删除保护', () => {
      template.hasResourceProperties('AWS::RDS::DBCluster', {
        DeletionProtection: true,
      });
    });

    it('Prod 环境应有 Writer + Reader (2 个实例)', () => {
      template.resourceCountIs('AWS::RDS::DBInstance', 2);
    });

    it('Prod 环境备份保留 30 天', () => {
      template.hasResourceProperties('AWS::RDS::DBCluster', {
        BackupRetentionPeriod: 30,
      });
    });
  });

  describe('公开属性', () => {
    it('应暴露 cluster, secret, clusterEndpoint', () => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const { vpc, securityGroup } = createTestDependencies(stack);

      const aurora = new AuroraConstruct(stack, 'TestAurora', {
        vpc,
        securityGroup,
        envName: 'dev',
      });

      expect(aurora.cluster).toBeDefined();
      expect(aurora.secret).toBeDefined();
      expect(aurora.clusterEndpoint).toBeDefined();
    });
  });

  describe('自定义参数', () => {
    it('应支持自定义数据库名称', () => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const { vpc, securityGroup } = createTestDependencies(stack);

      new AuroraConstruct(stack, 'TestAurora', {
        vpc,
        securityGroup,
        envName: 'dev',
        databaseName: 'custom_db',
      });
      const template = Template.fromStack(stack);

      template.hasResourceProperties('AWS::RDS::DBCluster', {
        DatabaseName: 'custom_db',
      });
    });

    it('默认数据库名称为 ai_agents_platform', () => {
      const app = new cdk.App();
      const stack = new cdk.Stack(app, 'TestStack');
      const { vpc, securityGroup } = createTestDependencies(stack);

      new AuroraConstruct(stack, 'TestAurora', {
        vpc,
        securityGroup,
        envName: 'dev',
      });
      const template = Template.fromStack(stack);

      template.hasResourceProperties('AWS::RDS::DBCluster', {
        DatabaseName: 'ai_agents_platform',
      });
    });
  });
});

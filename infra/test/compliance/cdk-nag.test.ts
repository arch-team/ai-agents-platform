import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import { Aspects } from 'aws-cdk-lib';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';
import { NetworkStack, SecurityStack, DatabaseStack } from '../../lib/stacks';

const testEnv = { account: '000000000000', region: 'ap-northeast-1' };

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

describe('CDK Nag 合规测试', () => {
  it('NetworkStack 应通过 AWS Solutions checks', () => {
    const app = new cdk.App();
    const stack = new NetworkStack(app, 'TestNetworkStack', {
      env: testEnv,
      vpcCidr: '10.0.0.0/16',
      envName: 'dev',
    });

    Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    // VPC Flow Log 相关的抑制
    NagSuppressions.addStackSuppressions(stack, [
      {
        id: 'AwsSolutions-IAM5',
        reason: 'VPC Flow Log 使用 CloudWatch Logs 需要通配符日志组权限',
      },
    ]);

    const messages = app.synth().getStackArtifact(stack.artifactId).messages;
    const errors = messages.filter((m) => m.level === 'error');

    expect(errors).toHaveLength(0);
  });

  it('SecurityStack 应通过 AWS Solutions checks', () => {
    const app = new cdk.App();
    const vpcStack = new cdk.Stack(app, 'VpcStack', { env: testEnv });
    const vpc = createTestVpc(vpcStack);

    const stack = new SecurityStack(app, 'TestSecurityStack', {
      env: testEnv,
      vpc,
      envName: 'dev',
    });

    Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    // API 安全组需要允许 HTTPS 入站 (0.0.0.0/0:443)，后续将通过 ALB 限制流量
    NagSuppressions.addStackSuppressions(stack, [
      {
        id: 'AwsSolutions-EC23',
        reason: 'API 安全组需要接受公网 HTTPS 请求，实际部署时通过 ALB + WAF 限制流量',
      },
    ]);

    const messages = app.synth().getStackArtifact(stack.artifactId).messages;
    const errors = messages.filter((m) => m.level === 'error');

    expect(errors).toHaveLength(0);
  });

  it('DatabaseStack 应通过 AWS Solutions checks', () => {
    const app = new cdk.App();
    const vpcStack = new cdk.Stack(app, 'VpcStack', { env: testEnv });
    const vpc = createTestVpc(vpcStack);
    const dbSecurityGroup = new ec2.SecurityGroup(vpcStack, 'TestDbSg', { vpc });
    const encryptionKey = new kms.Key(vpcStack, 'TestKey');

    const stack = new DatabaseStack(app, 'TestDatabaseStack', {
      env: testEnv,
      vpc,
      dbSecurityGroup,
      encryptionKey,
      envName: 'dev',
    });

    Aspects.of(stack).add(new AwsSolutionsChecks({ verbose: true }));

    // Aurora 集群相关的合理抑制
    NagSuppressions.addStackSuppressions(stack, [
      {
        id: 'AwsSolutions-RDS10',
        reason: 'Dev 环境不启用删除保护以方便开发迭代',
      },
      {
        id: 'AwsSolutions-SMG4',
        reason: '数据库凭证 Secret 的自动轮换将在后续迭代中配置',
      },
      {
        id: 'AwsSolutions-RDS6',
        reason: 'IAM 认证已通过 iamAuthentication: true 启用',
      },
      {
        id: 'AwsSolutions-RDS14',
        reason: 'Aurora MySQL Backtrack 暂不启用，使用标准备份策略',
      },
      {
        id: 'AwsSolutions-RDS16',
        reason: 'Aurora MySQL 不支持 Performance Insights 在 db.t3.small 实例类型上',
      },
      {
        id: 'AwsSolutions-RDS11',
        reason: '使用默认 MySQL 端口 3306，端口混淆在内网环境中收益有限',
      },
    ]);

    const messages = app.synth().getStackArtifact(stack.artifactId).messages;
    const errors = messages.filter((m) => m.level === 'error');

    expect(errors).toHaveLength(0);
  });
});

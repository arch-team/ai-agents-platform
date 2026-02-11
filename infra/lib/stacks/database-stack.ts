import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import type { BaseStackProps } from '../config';
import { AuroraConstruct } from '../constructs/aurora';
import type { DatabaseCluster } from 'aws-cdk-lib/aws-rds';
import type { ISecret } from 'aws-cdk-lib/aws-secretsmanager';

export interface DatabaseStackProps extends BaseStackProps {
  /** 数据库所在的 VPC */
  readonly vpc: ec2.IVpc;
  /** 数据库安全组 */
  readonly dbSecurityGroup: ec2.ISecurityGroup;
  /** KMS 加密密钥 */
  readonly encryptionKey?: kms.IKey;
}

/**
 * DatabaseStack - 数据库基础设施栈。
 * @remarks 包含 Aurora MySQL 集群。通过 Props 接收 VPC 和安全组依赖。
 */
export class DatabaseStack extends cdk.Stack {
  public readonly cluster: DatabaseCluster;
  public readonly dbSecret: ISecret;

  constructor(scope: Construct, id: string, props: DatabaseStackProps) {
    super(scope, id, props);

    const auroraConstruct = new AuroraConstruct(this, 'Aurora', {
      vpc: props.vpc,
      securityGroup: props.dbSecurityGroup,
      encryptionKey: props.encryptionKey,
      envName: props.envName,
    });

    this.cluster = auroraConstruct.cluster;
    this.dbSecret = auroraConstruct.secret;

    // CDK Nag 抑制
    this.suppressNagRules(auroraConstruct);

    // Outputs
    new cdk.CfnOutput(this, 'ClusterEndpoint', {
      value: auroraConstruct.clusterEndpoint.hostname,
      description: 'Aurora 集群端点',
    });
    new cdk.CfnOutput(this, 'SecretArn', {
      value: auroraConstruct.secret.secretArn,
      description: '数据库凭证 Secret ARN',
    });
  }

  /** CDK Nag 合规规则抑制 — Aurora 集群相关安全规则的合理豁免 */
  private suppressNagRules(auroraConstruct: AuroraConstruct): void {
    NagSuppressions.addResourceSuppressions(
      auroraConstruct.cluster,
      [
        {
          id: 'AwsSolutions-RDS10',
          reason: 'Dev 环境不启用删除保护以方便开发迭代; Prod 环境已启用',
        },
        {
          id: 'AwsSolutions-RDS11',
          reason: '使用默认 MySQL 端口 3306，数据库在 PRIVATE_ISOLATED 子网中，端口混淆收益有限',
        },
        {
          id: 'AwsSolutions-RDS14',
          reason: 'Aurora MySQL Backtrack 暂不启用，使用标准备份策略 (Dev 7 天 / Prod 30 天)',
        },
        {
          id: 'AwsSolutions-RDS16',
          reason: 'db.t3.small 实例类型不支持 Performance Insights，后续升级实例类型后启用',
        },
      ],
      true,
    );

    NagSuppressions.addResourceSuppressions(
      auroraConstruct,
      [
        {
          id: 'AwsSolutions-SMG4',
          reason: '数据库凭证 Secret 的自动轮换将在后续迭代中配置 Lambda 轮换函数',
        },
      ],
      true,
    );
  }
}

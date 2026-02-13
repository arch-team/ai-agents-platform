import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import type { BaseStackProps } from '../config';
import { AuroraConstruct } from '../constructs/aurora';

export interface DatabaseStackProps extends BaseStackProps {
  /** 数据库所在的 VPC */
  readonly vpc: ec2.IVpc;
  /** 数据库安全组 */
  readonly dbSecurityGroup: ec2.ISecurityGroup;
  /** KMS 加密密钥 */
  readonly encryptionKey?: kms.IKey;
  /** Aurora 实例类型 @default db.t3.medium (Dev), db.r6g.large (Prod) */
  readonly instanceType?: ec2.InstanceType;
}

/**
 * DatabaseStack - 数据库基础设施栈。
 * @remarks 包含 Aurora MySQL 集群。通过 Props 接收 VPC 和安全组依赖。
 */
export class DatabaseStack extends cdk.Stack {
  public readonly cluster: rds.DatabaseCluster;
  public readonly dbSecret: secretsmanager.ISecret;

  constructor(scope: Construct, id: string, props: DatabaseStackProps) {
    super(scope, id, props);

    const auroraConstruct = new AuroraConstruct(this, 'Aurora', {
      vpc: props.vpc,
      securityGroup: props.dbSecurityGroup,
      encryptionKey: props.encryptionKey,
      envName: props.envName,
      instanceType: props.instanceType,
    });

    this.cluster = auroraConstruct.cluster;
    this.dbSecret = auroraConstruct.secret;

    // CDK Nag 抑制
    this.suppressNagRules(auroraConstruct);

    // Outputs
    new cdk.CfnOutput(this, 'ClusterEndpoint', {
      value: auroraConstruct.clusterEndpoint.hostname,
      description: 'Aurora cluster endpoint',
    });
    new cdk.CfnOutput(this, 'SecretArn', {
      value: auroraConstruct.secret.secretArn,
      description: 'Database credentials Secret ARN',
    });
  }

  /** CDK Nag 合规规则抑制 — Aurora 集群相关安全规则的合理豁免 */
  private suppressNagRules(auroraConstruct: AuroraConstruct): void {
    NagSuppressions.addResourceSuppressions(
      auroraConstruct.cluster,
      [
        {
          id: 'AwsSolutions-RDS10',
          reason: 'Deletion protection disabled in Dev for easy iteration; enabled in Prod',
        },
        {
          id: 'AwsSolutions-RDS11',
          reason:
            'Using default MySQL port 3306; database is in PRIVATE_ISOLATED subnet, port obfuscation has limited benefit',
        },
        {
          id: 'AwsSolutions-RDS14',
          reason:
            'Aurora MySQL Backtrack not enabled; using standard backup policy (Dev 7 days / Prod 30 days)',
        },
        {
          id: 'AwsSolutions-RDS16',
          reason:
            'db.t3.small instance type does not support Performance Insights; will enable after instance upgrade',
        },
      ],
      true,
    );

    NagSuppressions.addResourceSuppressions(
      auroraConstruct,
      [
        {
          id: 'AwsSolutions-SMG4',
          reason:
            'Database credentials Secret auto-rotation will be configured with Lambda rotation function in future iteration',
        },
      ],
      true,
    );
  }
}

import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import type { BaseStackProps, EnvironmentName } from '../config';
import { getRemovalPolicy, isDev, isProd, PROJECT_NAME } from '../config';
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
 * DatabaseStack - 数据库与存储基础设施栈。
 * @remarks 包含 Aurora MySQL 集群和 S3 知识库文档存储。通过 Props 接收 VPC 和安全组依赖。
 */
export class DatabaseStack extends cdk.Stack {
  public readonly cluster: rds.DatabaseCluster;
  public readonly dbSecret: secretsmanager.ISecret;
  /** 知识库文档 S3 Bucket — 启用版本控制 */
  public readonly knowledgeBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: DatabaseStackProps) {
    super(scope, id, props);

    // --- Aurora MySQL 集群 ---
    const auroraConstruct = new AuroraConstruct(this, 'Aurora', {
      vpc: props.vpc,
      securityGroup: props.dbSecurityGroup,
      encryptionKey: props.encryptionKey,
      envName: props.envName,
      instanceType: props.instanceType,
      enablePerformanceInsights: isProd(props.envName),
    });

    this.cluster = auroraConstruct.cluster;
    this.dbSecret = auroraConstruct.secret;

    // --- S3 知识库文档存储 ---
    this.knowledgeBucket = new s3.Bucket(this, 'KnowledgeDocsBucket', {
      bucketName: `${PROJECT_NAME}-knowledge-${props.envName}`,
      versioned: true,
      encryption: props.encryptionKey ? s3.BucketEncryption.KMS : s3.BucketEncryption.S3_MANAGED,
      encryptionKey: props.encryptionKey,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      removalPolicy: getRemovalPolicy(props.envName),
      autoDeleteObjects: isDev(props.envName),
      lifecycleRules: [
        {
          // 旧版本 30 天后过期
          noncurrentVersionExpiration: cdk.Duration.days(30),
        },
        {
          // 未完成的分段上传 7 天后清理
          abortIncompleteMultipartUploadAfter: cdk.Duration.days(7),
        },
      ],
    });

    // CDK Nag 抑制
    this.suppressNagRules(auroraConstruct, props.envName);
    this.suppressKnowledgeBucketNagRules();

    // Outputs
    new cdk.CfnOutput(this, 'ClusterEndpoint', {
      value: auroraConstruct.clusterEndpoint.hostname,
      description: 'Aurora cluster endpoint',
    });
    new cdk.CfnOutput(this, 'SecretArn', {
      value: auroraConstruct.secret.secretArn,
      description: 'Database credentials Secret ARN',
    });
    new cdk.CfnOutput(this, 'KnowledgeBucketName', {
      value: this.knowledgeBucket.bucketName,
      description: 'Knowledge documents S3 bucket name',
    });
  }

  /** CDK Nag 合规规则抑制 — Aurora 集群相关安全规则的合理豁免 */
  private suppressNagRules(auroraConstruct: AuroraConstruct, envName: EnvironmentName): void {
    const suppressions = [
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
    ];

    // Performance Insights 仅 Prod 启用，Dev 环境抑制该规则
    if (!isProd(envName)) {
      suppressions.push({
        id: 'AwsSolutions-RDS16',
        reason:
          'Performance Insights disabled in Dev to reduce cost; enabled in Prod with db.r6g.large instances',
      });
    }

    NagSuppressions.addResourceSuppressions(auroraConstruct.cluster, suppressions, true);

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

  /** CDK Nag 合规規則抑制 — S3 知识库 Bucket 相关 */
  private suppressKnowledgeBucketNagRules(): void {
    NagSuppressions.addResourceSuppressions(this.knowledgeBucket, [
      {
        id: 'AwsSolutions-S1',
        reason:
          'Knowledge docs bucket does not require access logging; access is audited via CloudTrail',
      },
    ]);
  }
}

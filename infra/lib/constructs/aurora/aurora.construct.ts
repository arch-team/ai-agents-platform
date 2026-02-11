import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';
import { getRemovalPolicy, isDev, isProd } from '../../config/constants';

export interface AuroraConstructProps {
  /** Aurora 集群所在的 VPC */
  readonly vpc: ec2.IVpc;
  /** 数据库安全组 */
  readonly securityGroup: ec2.ISecurityGroup;
  /** KMS 加密密钥 */
  readonly encryptionKey?: kms.IKey;
  /** 环境名称 (dev, staging, prod) */
  readonly envName: string;
  /** 数据库名称 @default 'ai_agents_platform' */
  readonly databaseName?: string;
  /** 实例类型 @default db.t3.small */
  readonly instanceType?: ec2.InstanceType;
  /** 实例数量 @default 1 (Dev), 2 (Prod) */
  readonly instances?: number;
  /** 是否启用删除保护 @default envName !== 'dev' */
  readonly deletionProtection?: boolean;
}

/**
 * Aurora MySQL Construct - 创建 Aurora MySQL 3.x 集群。
 * @remarks Dev: db.t3.small 单 AZ; Prod: 多 AZ + 删除保护。
 */
export class AuroraConstruct extends Construct {
  public readonly cluster: rds.DatabaseCluster;
  public readonly secret: secretsmanager.ISecret;
  public readonly clusterEndpoint: rds.Endpoint;

  constructor(scope: Construct, id: string, props: AuroraConstructProps) {
    super(scope, id);

    const {
      vpc,
      securityGroup,
      encryptionKey,
      envName,
      databaseName = 'ai_agents_platform',
      instanceType = ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM),
      instances = isProd(envName) ? 2 : 1,
      deletionProtection = !isDev(envName),
    } = props;

    // Aurora MySQL 3.x 集群
    this.cluster = new rds.DatabaseCluster(this, 'Cluster', {
      engine: rds.DatabaseClusterEngine.auroraMysql({
        version: rds.AuroraMysqlEngineVersion.VER_3_10_0,
      }),
      credentials: rds.Credentials.fromGeneratedSecret('admin', {
        secretName: `${envName}/ai-agents-platform/db-credentials`,
      }),
      defaultDatabaseName: databaseName,
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      securityGroups: [securityGroup],
      writer: rds.ClusterInstance.provisioned('Writer', {
        instanceType,
        publiclyAccessible: false,
      }),
      readers:
        instances > 1
          ? [
              rds.ClusterInstance.provisioned('Reader', {
                instanceType,
                publiclyAccessible: false,
              }),
            ]
          : [],
      storageEncrypted: true,
      storageEncryptionKey: encryptionKey,
      deletionProtection,
      removalPolicy: getRemovalPolicy(envName),
      backup: {
        retention: isProd(envName) ? cdk.Duration.days(30) : cdk.Duration.days(7),
      },
      cloudwatchLogsExports: ['error', 'slowquery'],
      iamAuthentication: true,
    });

    const clusterSecret = this.cluster.secret;
    if (!clusterSecret) {
      throw new Error('Aurora 集群未生成 Secret，请检查 credentials 配置');
    }
    this.secret = clusterSecret;
    this.clusterEndpoint = this.cluster.clusterEndpoint;
  }
}

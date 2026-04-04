import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as efs from 'aws-cdk-lib/aws-efs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import { PROJECT_NAME, getRemovalPolicy, type BaseStackProps } from '../config';

export interface StorageStackProps extends BaseStackProps {
  /** EFS 挂载目标所在的 VPC */
  readonly vpc: ec2.IVpc;
}

/**
 * StorageStack - Agent Blueprint 存储基础设施栈。
 * @remarks 包含 S3 Workspace 存储桶 (AgentCore Runtime 下载 Agent 工作目录)
 *          和 EFS 文件系统 (ECS Web API 实时编辑 Skill Library + Agent Workspaces)。
 */
export class StorageStack extends cdk.Stack {
  /** S3 Workspace 存储桶 — Agent 工作目录持久化 */
  public readonly workspaceBucket: s3.Bucket;
  /** EFS 文件系统 — Skill Library + Agent Workspaces (ECS 挂载) */
  public readonly skillLibraryFs: efs.FileSystem;
  /** EFS 安全组 — 供 ComputeStack 添加入站规则 */
  public readonly efsSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props: StorageStackProps) {
    super(scope, id, props);
    const { vpc, envName } = props;

    // 1. S3 Bucket — Agent Workspace 持久化 (AgentCore Runtime 启动时下载)
    this.workspaceBucket = new s3.Bucket(this, 'WorkspaceBucket', {
      bucketName: `${PROJECT_NAME}-workspaces-${envName}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      versioned: true,
      removalPolicy: getRemovalPolicy(envName),
      autoDeleteObjects: envName === 'dev',
      lifecycleRules: [
        {
          // 归档 Agent 的 workspace 90 天后移入低频存储
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: cdk.Duration.days(90),
            },
          ],
        },
        {
          // 非当前版本 30 天后过期
          noncurrentVersionExpiration: cdk.Duration.days(30),
        },
        {
          // 不完整的分段上传 7 天后清理
          abortIncompleteMultipartUploadAfter: cdk.Duration.days(7),
        },
      ],
    });

    // 2. EFS FileSystem — Skill Library + Agent Workspaces (ECS 实时读写)
    this.efsSecurityGroup = new ec2.SecurityGroup(this, 'EfsSecurityGroup', {
      vpc,
      description: 'EFS Skill Library security group — allows NFS access from ECS',
      allowAllOutbound: false,
    });

    this.skillLibraryFs = new efs.FileSystem(this, 'SkillLibraryEfs', {
      vpc,
      encrypted: true,
      // Dev: Bursting 模式 (按需突发, 成本低); Prod 也用 Bursting (按需再升级)
      throughputMode: efs.ThroughputMode.BURSTING,
      performanceMode: efs.PerformanceMode.GENERAL_PURPOSE,
      removalPolicy: getRemovalPolicy(envName),
      securityGroup: this.efsSecurityGroup,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
    });

    // 3. CDK Nag 抑制
    this.suppressNagRules();

    // 4. Outputs
    new cdk.CfnOutput(this, 'WorkspaceBucketName', {
      value: this.workspaceBucket.bucketName,
      description: 'Workspace S3 Bucket 名称',
    });
    new cdk.CfnOutput(this, 'WorkspaceBucketArn', {
      value: this.workspaceBucket.bucketArn,
      description: 'Workspace S3 Bucket ARN',
    });
    new cdk.CfnOutput(this, 'SkillLibraryEfsId', {
      value: this.skillLibraryFs.fileSystemId,
      description: 'Skill Library EFS 文件系统 ID',
    });
  }

  /** CDK Nag 合规规则抑制 */
  private suppressNagRules(): void {
    // S3 Bucket: 未启用访问日志 (成本优化, 通过 CloudTrail 审计替代)
    NagSuppressions.addResourceSuppressions(this.workspaceBucket, [
      {
        id: 'AwsSolutions-S1',
        reason:
          'Workspace bucket access is audited via CloudTrail; dedicated access log bucket not needed for internal-only workspace storage',
      },
    ]);

    // S3 autoDeleteObjects Lambda: Dev 环境自动清理桶内容需要 Lambda + IAM 权限
    NagSuppressions.addResourceSuppressions(
      this,
      [
        {
          id: 'AwsSolutions-IAM4',
          reason:
            'Auto-delete objects custom resource Lambda uses AWS managed policy for log access (Dev environment only)',
        },
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Auto-delete objects custom resource requires s3:DeleteObject* and s3:GetObject* wildcards to clean bucket contents (Dev environment only)',
        },
        {
          id: 'AwsSolutions-L1',
          reason:
            'Auto-delete objects custom resource Lambda runtime is managed by CDK framework and uses the latest available runtime',
        },
      ],
      true,
    );
  }
}

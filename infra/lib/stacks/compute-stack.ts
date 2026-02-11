import * as path from 'path';
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import type { BaseStackProps } from '../config';
import { AlbConstruct } from '../constructs/alb';
import { EcsServiceConstruct } from '../constructs/ecs';

export interface ComputeStackProps extends BaseStackProps {
  /** ECS 服务所在的 VPC */
  readonly vpc: ec2.IVpc;
  /** 数据库安全组 — 用于添加 ECS → DB 入站规则 */
  readonly dbSecurityGroup: ec2.ISecurityGroup;
  /** 数据库凭证 Secret */
  readonly databaseSecret: secretsmanager.ISecret;
  /** 数据库连接端点 */
  readonly databaseEndpoint: string;
  /** KMS 加密密钥 */
  readonly encryptionKey: kms.IKey;
}

/**
 * ComputeStack - 计算基础设施栈。
 * @remarks 组合 ALB + ECS Fargate，部署后端 FastAPI 服务。通过 Props 接收 VPC、数据库和安全依赖。
 */
export class ComputeStack extends cdk.Stack {
  /** ALB DNS 名称 */
  public readonly albDnsName: string;
  /** ECS Fargate 服务 */
  public readonly service: ecs.FargateService;

  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    super(scope, id, props);

    const { vpc, dbSecurityGroup, databaseSecret, databaseEndpoint, encryptionKey, envName } =
      props;

    // ALB Construct
    const albConstruct = new AlbConstruct(this, 'Alb', {
      vpc,
      envName,
    });

    // ECS Service Construct
    const ecsConstruct = new EcsServiceConstruct(this, 'Ecs', {
      vpc,
      albSecurityGroup: albConstruct.albSecurityGroup,
      envName,
      containerImage: ecs.ContainerImage.fromAsset(path.join(__dirname, '../../..', 'backend'), {
        platform: cdk.aws_ecr_assets.Platform.LINUX_AMD64,
      }),
      environment: {
        APP_ENV: envName === 'prod' ? 'production' : 'development',
        DATABASE_HOST: databaseEndpoint,
        DATABASE_PORT: '3306',
        AWS_REGION: cdk.Stack.of(this).region,
        LOG_LEVEL: envName === 'prod' ? 'INFO' : 'DEBUG',
      },
      secrets: {
        // Aurora Secret JSON fields: host, port, username, password, dbname, engine
        DATABASE_USER: ecs.Secret.fromSecretsManager(databaseSecret, 'username'),
        DATABASE_PASSWORD: ecs.Secret.fromSecretsManager(databaseSecret, 'password'),
        DATABASE_NAME: ecs.Secret.fromSecretsManager(databaseSecret, 'dbname'),
        // JWT Secret — Dev 环境使用数据库密码作为临时 JWT key (后续 C-S4-3 统一管理)
        JWT_SECRET_KEY: ecs.Secret.fromSecretsManager(databaseSecret, 'password'),
      },
    });

    // 注册 ECS 服务到 ALB Target Group
    albConstruct.targetGroup.addTarget(ecsConstruct.service);

    // 允许 ECS 服务访问数据库 (3306)
    // 使用 CfnSecurityGroupIngress 避免跨 Stack 循环依赖
    new ec2.CfnSecurityGroupIngress(this, 'EcsToDbIngress', {
      groupId: dbSecurityGroup.securityGroupId,
      sourceSecurityGroupId: ecsConstruct.serviceSecurityGroup.securityGroupId,
      ipProtocol: 'tcp',
      fromPort: 3306,
      toPort: 3306,
      description: 'Allow ECS service to access Aurora MySQL',
    });

    // 授权 ECS Task 读取数据库 Secret
    databaseSecret.grantRead(ecsConstruct.service.taskDefinition.taskRole);

    // 授权 ECS Task 使用 KMS 解密
    encryptionKey.grantDecrypt(ecsConstruct.service.taskDefinition.taskRole);

    this.albDnsName = albConstruct.alb.loadBalancerDnsName;
    this.service = ecsConstruct.service;

    // CDK Nag 抑制
    this.suppressNagRules(albConstruct, ecsConstruct);

    // Outputs
    new cdk.CfnOutput(this, 'AlbDnsName', {
      value: albConstruct.alb.loadBalancerDnsName,
      description: 'ALB DNS name',
    });
    new cdk.CfnOutput(this, 'EcsClusterName', {
      value: ecsConstruct.cluster.clusterName,
      description: 'ECS cluster name',
    });
    new cdk.CfnOutput(this, 'ServiceName', {
      value: ecsConstruct.service.serviceName,
      description: 'ECS service name',
    });
  }

  /** CDK Nag 合规规则抑制 — ALB 和 ECS 相关安全规则的合理豁免 */
  private suppressNagRules(albConstruct: AlbConstruct, ecsConstruct: EcsServiceConstruct): void {
    // ALB: 未启用访问日志 (Dev 环境不需要)
    NagSuppressions.addResourceSuppressions(albConstruct.alb, [
      {
        id: 'AwsSolutions-ELB2',
        reason: 'ALB access logs not enabled in Dev; Prod will configure S3 access log bucket',
      },
    ]);

    // ALB: HTTP 而非 HTTPS (Dev 环境无域名/证书)
    NagSuppressions.addResourceSuppressions(albConstruct.httpListener, [
      {
        id: 'AwsSolutions-ELB1',
        reason: 'Dev uses HTTP (port 80); Prod will configure HTTPS + TLS certificate',
      },
    ]);

    // ECS Task Execution Role 使用 AWS 托管策略
    NagSuppressions.addResourceSuppressions(
      ecsConstruct.service.taskDefinition,
      [
        {
          id: 'AwsSolutions-IAM4',
          reason:
            'ECS Task Execution Role requires AmazonECSTaskExecutionRolePolicy managed policy to pull images and write logs',
        },
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'ECS Task Execution Role ecr:GetAuthorizationToken and logs:CreateLogStream require wildcard resources',
        },
      ],
      true,
    );

    // ECS Task Role 的 Secrets Manager 和 KMS 权限
    NagSuppressions.addResourceSuppressions(
      ecsConstruct.service.taskDefinition.taskRole,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Secrets Manager grantRead and KMS grantDecrypt generate policies with necessary wildcards (secretsmanager:GetSecretValue)',
        },
      ],
      true,
    );

    // ALB 安全组允许公网入站 (applyToChildren 确保覆盖底层 CfnResource)
    NagSuppressions.addResourceSuppressions(
      albConstruct.albSecurityGroup,
      [
        {
          id: 'AwsSolutions-EC23',
          reason: 'ALB is internet-facing and requires 0.0.0.0/0 HTTP inbound traffic',
        },
      ],
      true,
    );

    // ECS Task Definition 使用明文环境变量 (非敏感配置)
    NagSuppressions.addResourceSuppressions(
      ecsConstruct.service.taskDefinition,
      [
        {
          id: 'AwsSolutions-ECS2',
          reason:
            'ENV_NAME, DATABASE_HOST, DATABASE_PORT are non-sensitive config; no need to inject via Secrets Manager',
        },
      ],
      true,
    );
  }
}

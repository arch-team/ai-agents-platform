import * as path from 'path';
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import {
  BEDROCK_INVOKE_ACTIONS,
  getBedrockResourceArns,
  getCorsAllowedOrigins,
  type BaseStackProps,
} from '../config';
import { AlbConstruct } from '../constructs/alb';
import { EcsServiceConstruct, type ScheduledScalingConfig } from '../constructs/ecs';

export interface ComputeStackProps extends BaseStackProps {
  /** ECS 服务所在的 VPC */
  readonly vpc: ec2.IVpc;
  /** 数据库安全组 — 用于添加 ECS → DB 入站规则 */
  readonly dbSecurityGroup: ec2.ISecurityGroup;
  /** 数据库凭证 Secret */
  readonly databaseSecret: secretsmanager.ISecret;
  /** 数据库连接端点 */
  readonly databaseEndpoint: string;
  /** KMS 加密密钥 ARN — 使用 ARN 避免跨 Stack 循环依赖 */
  readonly encryptionKeyArn: string;
  /** JWT 签名密钥 ARN — 使用 ARN 避免跨 Stack 循环依赖 */
  readonly jwtSecretArn: string;
  /** Fargate CPU (256, 512, 1024, 2048, 4096) @default 256 */
  readonly cpu?: number;
  /** Fargate 内存 (MiB) @default 512 */
  readonly memoryLimitMiB?: number;
  /** 期望运行的任务数量 @default 1 */
  readonly desiredCount?: number;
  /** 定时缩放配置 — Dev 环境非工作时段自动缩减 ECS 任务数 */
  readonly scheduledScaling?: ScheduledScalingConfig;
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
  /** Application Load Balancer */
  public readonly loadBalancer: elbv2.ApplicationLoadBalancer;
  /** ALB Target Group */
  public readonly targetGroup: elbv2.ApplicationTargetGroup;

  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    super(scope, id, props);

    const {
      vpc,
      dbSecurityGroup,
      databaseSecret,
      databaseEndpoint,
      encryptionKeyArn,
      jwtSecretArn,
      envName,
    } = props;

    // 在本 Stack 内重新导入 Security 资源，避免跨 Stack grant* 循环依赖
    const jwtSecret = secretsmanager.Secret.fromSecretCompleteArn(this, 'JwtSecretRef', jwtSecretArn);
    const encryptionKey = kms.Key.fromKeyArn(this, 'EncryptionKeyRef', encryptionKeyArn);

    // ALB Construct (先创建，ECS 需要引用其安全组配置入站规则)
    // ecsSecurityGroup 在 ECS 创建后通过 Stack 层组装添加出站规则
    const albConstruct = new AlbConstruct(this, 'Alb', {
      vpc,
      envName,
    });

    // ECS Service Construct
    const ecsConstruct = new EcsServiceConstruct(this, 'Ecs', {
      vpc,
      albSecurityGroup: albConstruct.albSecurityGroup,
      envName,
      cpu: props.cpu,
      memoryLimitMiB: props.memoryLimitMiB,
      desiredCount: props.desiredCount,
      scheduledScaling: props.scheduledScaling,
      containerImage: ecs.ContainerImage.fromAsset(path.join(__dirname, '../../..', 'backend'), {
        platform: cdk.aws_ecr_assets.Platform.LINUX_AMD64,
      }),
      environment: {
        APP_ENV: envName === 'prod' ? 'production' : 'development',
        DATABASE_HOST: databaseEndpoint,
        DATABASE_PORT: '3306',
        AWS_REGION: cdk.Stack.of(this).region,
        LOG_LEVEL: envName === 'prod' ? 'INFO' : 'DEBUG',
        // CORS: 前端 S3 静态站点域名 (从 config/constants 集中管理)
        CORS_ALLOWED_ORIGINS: JSON.stringify(getCorsAllowedOrigins(envName)),
        // Secrets Manager ARN — 应用可选择直接读取 (备用路径, ECS Secrets 为主路径)
        DB_SECRET_ARN: databaseSecret.secretArn,
        JWT_SECRET_ARN: jwtSecret.secretArn,
      },
      secrets: {
        // Aurora Secret JSON fields: host, port, username, password, dbname, engine
        DATABASE_USER: ecs.Secret.fromSecretsManager(databaseSecret, 'username'),
        DATABASE_PASSWORD: ecs.Secret.fromSecretsManager(databaseSecret, 'password'),
        DATABASE_NAME: ecs.Secret.fromSecretsManager(databaseSecret, 'dbname'),
        // JWT Secret — 独立管理，从 SecurityStack 的 Secrets Manager 注入
        JWT_SECRET_KEY: ecs.Secret.fromSecretsManager(jwtSecret, 'secret_key'),
      },
    });

    // Stack 层组装: ALB → ECS 显式出站规则 (安全组出站收窄)
    albConstruct.albSecurityGroup.addEgressRule(
      ecsConstruct.serviceSecurityGroup,
      ec2.Port.tcp(ecsConstruct.containerPort),
      'Allow ALB to forward traffic to ECS containers',
    );

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

    // 授权 ECS Task Role 读取数据库 Secret 和 JWT Secret (应用运行时访问)
    // jwtSecret/encryptionKey 已在本 Stack 内通过 ARN 重新导入，grant 不会跨 Stack
    databaseSecret.grantRead(ecsConstruct.service.taskDefinition.taskRole);
    jwtSecret.grantRead(ecsConstruct.service.taskDefinition.taskRole);
    encryptionKey.grantDecrypt(ecsConstruct.service.taskDefinition.taskRole);

    // 授权 ECS Execution Role 解密 KMS 密钥 (容器启动时注入 Secrets Manager 环境变量)
    // JWT Secret 使用自定义 KMS key 加密，Execution Role 需要 kms:Decrypt 才能读取
    encryptionKey.grantDecrypt(ecsConstruct.service.taskDefinition.executionRole!);

    // 授权 ECS Task Role 调用 Bedrock (Claude Agent SDK + Agent Teams 所需)
    // 参考: claude-code-bedrock-container.md — IAM inference-profile 权限
    const accountId = cdk.Stack.of(this).account;
    ecsConstruct.service.taskDefinition.taskRole.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: [...BEDROCK_INVOKE_ACTIONS],
        resources: getBedrockResourceArns(accountId),
      }),
    );

    this.albDnsName = albConstruct.alb.loadBalancerDnsName;
    this.service = ecsConstruct.service;
    this.loadBalancer = albConstruct.alb;
    this.targetGroup = albConstruct.targetGroup;

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
            'Secrets Manager grantRead (database + JWT secrets) and KMS grantDecrypt generate policies with necessary wildcards',
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

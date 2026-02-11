import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';
import { getRemovalPolicy } from '../../config/constants';

export interface EcsServiceConstructProps {
  /** ECS 服务所在的 VPC */
  readonly vpc: ec2.IVpc;
  /** ALB 安全组，用于配置 ECS 安全组的入站规则 */
  readonly albSecurityGroup: ec2.ISecurityGroup;
  /** 环境名称 (dev, staging, prod) */
  readonly envName: string;
  /** 容器镜像 */
  readonly containerImage: ecs.ContainerImage;
  /** 容器端口 @default 8000 */
  readonly containerPort?: number;
  /** Fargate CPU (256, 512, 1024, 2048, 4096) @default 256 */
  readonly cpu?: number;
  /** Fargate 内存 (MiB) @default 512 */
  readonly memoryLimitMiB?: number;
  /** 期望运行的任务数量 @default 1 */
  readonly desiredCount?: number;
  /** 容器环境变量 */
  readonly environment?: Record<string, string>;
  /** 容器 Secrets (从 Secrets Manager 注入) */
  readonly secrets?: Record<string, ecs.Secret>;
}

/**
 * ECS Fargate Service Construct - 创建 ECS 集群和 Fargate 服务。
 * @remarks Dev: 256 CPU, 512 MiB; 日志保留 1 周。服务运行在 PRIVATE_WITH_EGRESS 子网。
 */
export class EcsServiceConstruct extends Construct {
  /** ECS 集群 */
  public readonly cluster: ecs.Cluster;
  /** Fargate 服务 */
  public readonly service: ecs.FargateService;
  /** ECS 服务安全组 */
  public readonly serviceSecurityGroup: ec2.SecurityGroup;
  /** 容器端口 */
  public readonly containerPort: number;

  constructor(scope: Construct, id: string, props: EcsServiceConstructProps) {
    super(scope, id);

    const {
      vpc,
      albSecurityGroup,
      envName,
      containerImage,
      containerPort = 8000,
      cpu = 256,
      memoryLimitMiB = 512,
      desiredCount = 1,
      environment = {},
      secrets = {},
    } = props;

    this.containerPort = containerPort;

    // ECS 集群
    this.cluster = new ecs.Cluster(this, 'Cluster', {
      vpc,
      clusterName: `ai-agents-${envName}`,
      containerInsightsV2: ecs.ContainerInsights.ENABLED,
    });

    // ECS 服务安全组 — 仅允许来自 ALB 的入站
    this.serviceSecurityGroup = new ec2.SecurityGroup(this, 'ServiceSg', {
      vpc,
      description: 'ECS Fargate service security group - ALB ingress only',
      allowAllOutbound: true,
    });
    this.serviceSecurityGroup.addIngressRule(
      albSecurityGroup,
      ec2.Port.tcp(containerPort),
      'Allow ALB to access container port',
    );

    // CloudWatch 日志组
    const logGroup = new logs.LogGroup(this, 'LogGroup', {
      logGroupName: `/ecs/ai-agents-platform/${envName}`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: getRemovalPolicy(envName),
    });

    // Fargate Task Definition
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'TaskDef', {
      cpu,
      memoryLimitMiB,
    });

    taskDefinition.addContainer('ApiContainer', {
      image: containerImage,
      containerName: 'api',
      portMappings: [{ containerPort }],
      environment,
      secrets,
      logging: ecs.LogDrivers.awsLogs({
        logGroup,
        streamPrefix: 'api',
      }),
      healthCheck: {
        command: ['CMD-SHELL', `curl -f http://localhost:${containerPort}/health || exit 1`],
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        retries: 3,
        startPeriod: cdk.Duration.seconds(60),
      },
    });

    // Fargate 服务
    this.service = new ecs.FargateService(this, 'Service', {
      cluster: this.cluster,
      taskDefinition,
      desiredCount,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [this.serviceSecurityGroup],
      assignPublicIp: false,
    });
  }
}

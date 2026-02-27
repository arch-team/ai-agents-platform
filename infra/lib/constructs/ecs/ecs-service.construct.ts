import * as cdk from 'aws-cdk-lib';
import * as appscaling from 'aws-cdk-lib/aws-applicationautoscaling';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';
import { getLogRetention, getRemovalPolicy, type EnvironmentName } from '../../config';

/** 定时缩放配置 — 用于 Dev 环境非工作时段自动缩减 ECS 任务数 */
export interface ScheduledScalingConfig {
  /** 缩减 cron 表达式 (UTC 时间) */
  readonly scaleDownSchedule: string;
  /** 恢复 cron 表达式 (UTC 时间) */
  readonly scaleUpSchedule: string;
  /** 缩减时的最小任务数 @default 0 */
  readonly scaleDownMinCapacity?: number;
  /** 恢复时的最小任务数 */
  readonly scaleUpMinCapacity: number;
  /** 恢复时的最大任务数 */
  readonly scaleUpMaxCapacity: number;
}

export interface EcsServiceConstructProps {
  /** ECS 服务所在的 VPC */
  readonly vpc: ec2.IVpc;
  /** ALB 安全组，用于配置 ECS 安全组的入站规则 */
  readonly albSecurityGroup: ec2.ISecurityGroup;
  /** 环境名称 (dev | prod) */
  readonly envName: EnvironmentName;
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
  /** 自定义容器健康检查命令 @default ['CMD-SHELL', 'python -c "import httpx; httpx.get(\'http://localhost:{port}/health\').raise_for_status()" || exit 1'] */
  readonly healthCheckCommand?: string[];
  /** 定时缩放配置 — Dev 环境非工作时段自动缩减 ECS 任务数以降低成本 @default undefined (不启用定时缩放) */
  readonly scheduledScaling?: ScheduledScalingConfig;
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
      healthCheckCommand,
    } = props;

    this.containerPort = containerPort;

    this.cluster = new ecs.Cluster(this, 'Cluster', {
      vpc,
      clusterName: `ai-agents-${envName}`,
      containerInsightsV2: ecs.ContainerInsights.ENABLED,
    });

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

    const logGroup = new logs.LogGroup(this, 'LogGroup', {
      logGroupName: `/ecs/ai-agents-platform/${envName}`,
      retention: getLogRetention(envName),
      removalPolicy: getRemovalPolicy(envName),
    });

    const taskDefinition = new ecs.FargateTaskDefinition(this, 'TaskDef', {
      cpu,
      memoryLimitMiB,
    });

    // 注入 tini 作为 PID 1, 回收 CLI 僵尸子进程 + 正确传播 SIGTERM
    const linuxParameters = new ecs.LinuxParameters(this, 'LinuxParams', {
      initProcessEnabled: true,
    });

    taskDefinition.addContainer('ApiContainer', {
      image: containerImage,
      containerName: 'api',
      portMappings: [{ containerPort }],
      environment,
      secrets,
      linuxParameters,
      logging: ecs.LogDrivers.awsLogs({
        logGroup,
        streamPrefix: 'api',
      }),
      healthCheck: {
        command: healthCheckCommand ?? [
          'CMD-SHELL',
          `python -c "import httpx; httpx.get('http://localhost:${containerPort}/health').raise_for_status()" || exit 1`,
        ],
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        retries: 3,
        startPeriod: cdk.Duration.seconds(60),
      },
    });

    this.service = new ecs.FargateService(this, 'Service', {
      cluster: this.cluster,
      taskDefinition,
      desiredCount,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [this.serviceSecurityGroup],
      assignPublicIp: false,
      // 部署 CircuitBreaker — 部署失败时自动回滚到上一个稳定版本
      circuitBreaker: { rollback: true },
      // 滚动更新参数 — 保证部署期间至少有 100% 健康任务，最多 200%
      minHealthyPercent: 100,
      maxHealthyPercent: 200,
    });

    // 定时缩放 — Dev 环境非工作时段自动缩减任务数以降低成本
    if (props.scheduledScaling) {
      const {
        scaleDownSchedule,
        scaleUpSchedule,
        scaleDownMinCapacity = 0,
        scaleUpMinCapacity,
        scaleUpMaxCapacity,
      } = props.scheduledScaling;

      const scalableTarget = this.service.autoScaleTaskCount({
        minCapacity: scaleDownMinCapacity,
        maxCapacity: scaleUpMaxCapacity,
      });

      scalableTarget.scaleOnSchedule('ScaleDown', {
        schedule: appscaling.Schedule.expression(`cron(${scaleDownSchedule})`),
        minCapacity: scaleDownMinCapacity,
        maxCapacity: scaleDownMinCapacity,
      });

      scalableTarget.scaleOnSchedule('ScaleUp', {
        schedule: appscaling.Schedule.expression(`cron(${scaleUpSchedule})`),
        minCapacity: scaleUpMinCapacity,
        maxCapacity: scaleUpMaxCapacity,
      });
    }
  }
}

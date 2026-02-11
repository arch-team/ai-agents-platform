import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import { Construct } from 'constructs';
import type { EnvironmentName } from '../../config/types';

export interface AlbConstructProps {
  /** ALB 所在的 VPC */
  readonly vpc: ec2.IVpc;
  /** 环境名称 (dev, staging, prod) */
  readonly envName: EnvironmentName;
  /** ECS 服务安全组 — 用于添加 ALB → ECS 的显式出站规则 */
  readonly ecsSecurityGroup?: ec2.ISecurityGroup;
  /** ECS 容器端口 @default 8000 */
  readonly containerPort?: number;
  /** ACM 证书 ARN — 提供时启用 HTTPS，HTTP 自动重定向到 HTTPS */
  readonly certificateArn?: string;
  /** 自定义域名 (与 certificateArn 配合使用) */
  readonly domainName?: string;
}

/**
 * Application Load Balancer Construct - 创建面向公网的 ALB。
 * @remarks
 * - 在 PUBLIC 子网创建 internet-facing ALB
 * - 安全组出站规则收窄: 仅允许到 ECS 安全组的流量 (需传入 ecsSecurityGroup)
 * - 提供 certificateArn 时自动创建 HTTPS Listener，HTTP 重定向到 HTTPS
 * - 未提供 certificateArn 时保持 HTTP-only 模式
 */
export class AlbConstruct extends Construct {
  /** Application Load Balancer */
  public readonly alb: elbv2.ApplicationLoadBalancer;
  /** ALB 安全组 */
  public readonly albSecurityGroup: ec2.SecurityGroup;
  /** HTTP Listener */
  public readonly httpListener: elbv2.ApplicationListener;
  /** HTTPS Listener (仅在提供 certificateArn 时创建) */
  public readonly httpsListener?: elbv2.ApplicationListener;
  /** Target Group */
  public readonly targetGroup: elbv2.ApplicationTargetGroup;

  constructor(scope: Construct, id: string, props: AlbConstructProps) {
    super(scope, id);

    const { vpc, envName, ecsSecurityGroup, containerPort = 8000, certificateArn } = props;

    // ALB 安全组 — 出站规则收窄，不允许全部出站
    this.albSecurityGroup = new ec2.SecurityGroup(this, 'AlbSg', {
      vpc,
      description: 'ALB security group - public HTTP ingress',
      allowAllOutbound: false,
    });
    this.albSecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(80),
      'Allow public HTTP ingress',
    );

    // 显式出站规则: ALB → ECS 安全组 (健康检查 + 转发流量)
    if (ecsSecurityGroup) {
      this.albSecurityGroup.addEgressRule(
        ecsSecurityGroup,
        ec2.Port.tcp(containerPort),
        'Allow ALB to forward traffic to ECS containers',
      );
    }

    // 提供证书时，允许 HTTPS 入站
    if (certificateArn) {
      this.albSecurityGroup.addIngressRule(
        ec2.Peer.anyIpv4(),
        ec2.Port.tcp(443),
        'Allow public HTTPS ingress',
      );
    }

    // Application Load Balancer — 使用手动创建的安全组，避免 ALB 自动创建默认 SG
    this.alb = new elbv2.ApplicationLoadBalancer(this, 'Alb', {
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      internetFacing: true,
      loadBalancerName: `ai-agents-${envName}`,
      securityGroup: this.albSecurityGroup,
    });

    // Target Group
    this.targetGroup = new elbv2.ApplicationTargetGroup(this, 'TargetGroup', {
      vpc,
      port: containerPort,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targetType: elbv2.TargetType.IP,
      healthCheck: {
        path: '/health',
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        healthyThresholdCount: 2,
        unhealthyThresholdCount: 3,
        healthyHttpCodes: '200',
      },
    });

    if (certificateArn) {
      // HTTPS 模式: HTTPS Listener (443) + HTTP 重定向到 HTTPS
      this.httpsListener = this.alb.addListener('HttpsListener', {
        port: 443,
        protocol: elbv2.ApplicationProtocol.HTTPS,
        certificates: [elbv2.ListenerCertificate.fromArn(certificateArn)],
        sslPolicy: elbv2.SslPolicy.TLS12,
        defaultTargetGroups: [this.targetGroup],
      });

      this.httpListener = this.alb.addListener('HttpListener', {
        port: 80,
        defaultAction: elbv2.ListenerAction.redirect({
          protocol: 'HTTPS',
          port: '443',
          permanent: true,
        }),
      });
    } else {
      // HTTP-only 模式 (Dev 环境无域名/证书)
      this.httpListener = this.alb.addListener('HttpListener', {
        port: 80,
        defaultTargetGroups: [this.targetGroup],
      });
    }
  }
}

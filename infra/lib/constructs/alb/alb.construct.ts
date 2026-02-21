import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import { Construct } from 'constructs';
import type { EnvironmentName } from '../../config';

export interface AlbConstructProps {
  /** ALB 所在的 VPC */
  readonly vpc: ec2.IVpc;
  /** 环境名称 (dev | prod) */
  readonly envName: EnvironmentName;
  /** ECS 服务安全组 — 用于添加 ALB → ECS 的显式出站规则 @default undefined (不创建出站规则) */
  readonly ecsSecurityGroup?: ec2.ISecurityGroup;
  /** ECS 容器端口 @default 8000 */
  readonly containerPort?: number;
  /** ACM 证书 ARN — 提供时启用 HTTPS，HTTP 自动重定向到 HTTPS @default undefined (HTTP-only 模式) */
  readonly certificateArn?: string;
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

    if (ecsSecurityGroup) {
      this.albSecurityGroup.addEgressRule(
        ecsSecurityGroup,
        ec2.Port.tcp(containerPort),
        'Allow ALB to forward traffic to ECS containers',
      );
    }

    if (certificateArn) {
      this.albSecurityGroup.addIngressRule(
        ec2.Peer.anyIpv4(),
        ec2.Port.tcp(443),
        'Allow public HTTPS ingress',
      );
    }

    this.alb = new elbv2.ApplicationLoadBalancer(this, 'Alb', {
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      internetFacing: true,
      loadBalancerName: `ai-agents-${envName}`,
      securityGroup: this.albSecurityGroup,
    });

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
      this.httpListener = this.alb.addListener('HttpListener', {
        port: 80,
        defaultTargetGroups: [this.targetGroup],
      });
    }
  }
}

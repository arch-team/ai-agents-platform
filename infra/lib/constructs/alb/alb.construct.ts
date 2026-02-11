import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import { Construct } from 'constructs';

export interface AlbConstructProps {
  /** ALB 所在的 VPC */
  readonly vpc: ec2.IVpc;
  /** 环境名称 (dev, staging, prod) */
  readonly envName: string;
}

/**
 * Application Load Balancer Construct - 创建面向公网的 ALB。
 * @remarks 在 PUBLIC 子网创建 internet-facing ALB，HTTP Listener 端口 80。
 */
export class AlbConstruct extends Construct {
  /** Application Load Balancer */
  public readonly alb: elbv2.ApplicationLoadBalancer;
  /** ALB 安全组 */
  public readonly albSecurityGroup: ec2.SecurityGroup;
  /** HTTP Listener */
  public readonly httpListener: elbv2.ApplicationListener;
  /** Target Group */
  public readonly targetGroup: elbv2.ApplicationTargetGroup;

  constructor(scope: Construct, id: string, props: AlbConstructProps) {
    super(scope, id);

    const { vpc, envName } = props;

    // ALB 安全组 — 允许公网 HTTP 入站
    this.albSecurityGroup = new ec2.SecurityGroup(this, 'AlbSg', {
      vpc,
      description: 'ALB security group - public HTTP ingress',
      allowAllOutbound: true,
    });
    this.albSecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(80),
      '允许公网 HTTP 入站',
    );

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
      port: 8000,
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

    // HTTP Listener
    this.httpListener = this.alb.addListener('HttpListener', {
      port: 80,
      defaultTargetGroups: [this.targetGroup],
    });
  }
}

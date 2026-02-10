import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';

export interface SecurityGroupsConstructProps {
  /** 安全组所在的 VPC */
  readonly vpc: ec2.IVpc;
  /** 是否启用公网入站规则 (0.0.0.0/0:443) @default false */
  readonly enablePublicIngress?: boolean;
}

/**
 * Security Groups Construct - 创建平台安全组。
 * @remarks 最小权限原则，仅开放必要端口。
 */
export class SecurityGroupsConstruct extends Construct {
  /** API 服务安全组 (ECS/Lambda) */
  public readonly apiSecurityGroup: ec2.SecurityGroup;
  /** 数据库安全组 (Aurora) */
  public readonly dbSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props: SecurityGroupsConstructProps) {
    super(scope, id);
    const { vpc, enablePublicIngress = false } = props;

    // API 服务安全组
    // TODO: 后续创建 ALB 后，收窄出站规则为仅允许访问必要的 AWS 服务端点
    this.apiSecurityGroup = new ec2.SecurityGroup(this, 'ApiSg', {
      vpc,
      description: 'API 服务安全组',
      allowAllOutbound: true,
    });

    // 仅在启用公网入站时添加 0.0.0.0/0 入站规则
    // TODO: 后续创建 ALB 后，将入站来源改为 ALB 安全组而非 0.0.0.0/0
    if (enablePublicIngress) {
      this.apiSecurityGroup.addIngressRule(
        ec2.Peer.anyIpv4(),
        ec2.Port.tcp(443),
        '允许 HTTPS 入站',
      );
    }

    // 数据库安全组 - 仅允许 API 服务访问
    this.dbSecurityGroup = new ec2.SecurityGroup(this, 'DbSg', {
      vpc,
      description: '数据库安全组 - 仅允许 API 服务访问',
      allowAllOutbound: false,
    });
    this.dbSecurityGroup.addIngressRule(
      this.apiSecurityGroup,
      ec2.Port.tcp(3306),
      '允许 API 服务访问 MySQL',
    );
  }
}

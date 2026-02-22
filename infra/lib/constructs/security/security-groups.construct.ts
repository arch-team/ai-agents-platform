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
 *   - API SG: allowAllOutbound=true 覆盖 AWS 服务端点、外部 API 及 LDAP (389/636) 出站（SSO 所需）
 *   - DB SG: 仅允许 API SG 访问 MySQL 3306
 */
export class SecurityGroupsConstruct extends Construct {
  /** API 服务安全组 (ECS/Lambda) */
  public readonly apiSecurityGroup: ec2.SecurityGroup;
  /** 数据库安全组 (Aurora) */
  public readonly dbSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props: SecurityGroupsConstructProps) {
    super(scope, id);
    const { vpc, enablePublicIngress = false } = props;

    // API 服务安全组 — 出站允许全部（需访问 AWS 服务端点、外部 API 等）
    this.apiSecurityGroup = new ec2.SecurityGroup(this, 'ApiSg', {
      vpc,
      description: 'API service security group',
      allowAllOutbound: true,
    });

    if (enablePublicIngress) {
      this.apiSecurityGroup.addIngressRule(
        ec2.Peer.anyIpv4(),
        ec2.Port.tcp(443),
        'Allow HTTPS ingress',
      );
    }

    this.dbSecurityGroup = new ec2.SecurityGroup(this, 'DbSg', {
      vpc,
      description: 'Database security group - API service access only',
      allowAllOutbound: false,
    });
    this.dbSecurityGroup.addIngressRule(
      this.apiSecurityGroup,
      ec2.Port.tcp(3306),
      'Allow API service to access MySQL',
    );
  }
}

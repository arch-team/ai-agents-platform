import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import { KmsConstruct } from '../constructs/security/kms.construct';
import { SecurityGroupsConstruct } from '../constructs/security/security-groups.construct';

export interface SecurityStackProps extends cdk.StackProps {
  /** 安全组所在的 VPC */
  readonly vpc: ec2.IVpc;
  /** 环境名称 (dev, staging, prod) */
  readonly envName: string;
}

/**
 * SecurityStack - 安全基础设施栈。
 * @remarks 包含 KMS 加密密钥和安全组。Prod 环境额外创建 Secrets Manager VPC Endpoint。
 */
export class SecurityStack extends cdk.Stack {
  public readonly encryptionKey: kms.Key;
  public readonly apiSecurityGroup: ec2.SecurityGroup;
  public readonly dbSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props: SecurityStackProps) {
    super(scope, id, props);
    const { vpc, envName } = props;

    // KMS 加密密钥
    const kmsConstruct = new KmsConstruct(this, 'Kms', {
      alias: `ai-agents-platform-${envName}`,
    });
    this.encryptionKey = kmsConstruct.key;

    // 安全组
    const sgConstruct = new SecurityGroupsConstruct(this, 'SecurityGroups', { vpc });
    this.apiSecurityGroup = sgConstruct.apiSecurityGroup;
    this.dbSecurityGroup = sgConstruct.dbSecurityGroup;

    // VPC Endpoints (Secrets Manager - Prod 环境)
    if (envName === 'prod') {
      new ec2.InterfaceVpcEndpoint(this, 'SecretsManagerEndpoint', {
        vpc,
        service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
      });
    }

    // CDK Nag 抑制: API 安全组允许公网 HTTPS 入站
    NagSuppressions.addResourceSuppressions(this.apiSecurityGroup, [
      {
        id: 'AwsSolutions-EC23',
        reason: 'API 安全组需要接受公网 HTTPS 请求 (443)，实际部署时通过 ALB + WAF 限制流量',
      },
    ]);

    // Outputs
    new cdk.CfnOutput(this, 'EncryptionKeyArn', {
      value: this.encryptionKey.keyArn,
      description: 'KMS 加密密钥 ARN',
    });
  }
}

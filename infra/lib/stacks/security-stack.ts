import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import { Construct } from 'constructs';
import type { BaseStackProps } from '../config/types';
import { KmsConstruct, SecurityGroupsConstruct } from '../constructs/security';

export interface SecurityStackProps extends BaseStackProps {
  /** 安全组所在的 VPC */
  readonly vpc: ec2.IVpc;
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
      envName,
      alias: `ai-agents-platform-${envName}`,
    });
    this.encryptionKey = kmsConstruct.key;

    // 安全组
    // TODO: 后续创建 ALB 后将 enablePublicIngress 设为 true
    const sgConstruct = new SecurityGroupsConstruct(this, 'SecurityGroups', {
      vpc,
      enablePublicIngress: false,
    });
    this.apiSecurityGroup = sgConstruct.apiSecurityGroup;
    this.dbSecurityGroup = sgConstruct.dbSecurityGroup;

    // VPC Endpoints (Secrets Manager - Prod 环境)
    if (envName === 'prod') {
      new ec2.InterfaceVpcEndpoint(this, 'SecretsManagerEndpoint', {
        vpc,
        service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
      });
    }

    // Outputs
    new cdk.CfnOutput(this, 'EncryptionKeyArn', {
      value: this.encryptionKey.keyArn,
      description: 'KMS 加密密钥 ARN',
    });
  }
}

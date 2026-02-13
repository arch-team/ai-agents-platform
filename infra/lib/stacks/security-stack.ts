import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import { isProd, type BaseStackProps } from '../config';
import { KmsConstruct, SecurityGroupsConstruct } from '../constructs/security';

export interface SecurityStackProps extends BaseStackProps {
  /** 安全组所在的 VPC */
  readonly vpc: ec2.IVpc;
}

/**
 * SecurityStack - 安全基础设施栈。
 * @remarks 包含 KMS 加密密钥、安全组和 JWT Secret。Prod 环境额外创建 Secrets Manager VPC Endpoint。
 */
export class SecurityStack extends cdk.Stack {
  public readonly encryptionKey: kms.Key;
  public readonly apiSecurityGroup: ec2.SecurityGroup;
  public readonly dbSecurityGroup: ec2.SecurityGroup;
  /** JWT 签名密钥 (Secrets Manager) */
  public readonly jwtSecret: secretsmanager.Secret;

  constructor(scope: Construct, id: string, props: SecurityStackProps) {
    super(scope, id, props);
    const { vpc, envName } = props;

    const kmsConstruct = new KmsConstruct(this, 'Kms', {
      envName,
      alias: `ai-agents-platform-${envName}`,
    });
    this.encryptionKey = kmsConstruct.key;

    const sgConstruct = new SecurityGroupsConstruct(this, 'SecurityGroups', {
      vpc,
      enablePublicIngress: false,
    });
    this.apiSecurityGroup = sgConstruct.apiSecurityGroup;
    this.dbSecurityGroup = sgConstruct.dbSecurityGroup;

    // JWT 签名密钥
    this.jwtSecret = new secretsmanager.Secret(this, 'JwtSecret', {
      secretName: `${envName}/ai-platform/jwt-secret`,
      description: 'JWT 签名密钥 — 用于 API 认证 Token 签发和验证',
      generateSecretString: {
        secretStringTemplate: JSON.stringify({}),
        generateStringKey: 'secret_key',
        passwordLength: 64,
        excludePunctuation: true,
      },
      encryptionKey: this.encryptionKey,
    });

    NagSuppressions.addResourceSuppressions(this.jwtSecret, [
      {
        id: 'AwsSolutions-SMG4',
        reason:
          'JWT signing secret does not require automatic rotation; key rotation is handled at application deployment level',
      },
    ]);

    if (isProd(envName)) {
      new ec2.InterfaceVpcEndpoint(this, 'SecretsManagerEndpoint', {
        vpc,
        service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
      });
    }

    new cdk.CfnOutput(this, 'EncryptionKeyArn', {
      value: this.encryptionKey.keyArn,
      description: 'KMS encryption key ARN',
    });
    new cdk.CfnOutput(this, 'JwtSecretArn', {
      value: this.jwtSecret.secretArn,
      description: 'JWT signing secret ARN',
    });
  }
}

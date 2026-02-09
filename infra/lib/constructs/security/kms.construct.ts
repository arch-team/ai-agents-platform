import * as cdk from 'aws-cdk-lib';
import * as kms from 'aws-cdk-lib/aws-kms';
import { Construct } from 'constructs';

export interface KmsConstructProps {
  /** KMS 密钥别名 @default 'ai-agents-platform' */
  readonly alias?: string;
  /** 是否启用自动密钥轮换 @default true */
  readonly enableKeyRotation?: boolean;
}

/**
 * KMS Construct - 创建平台加密主密钥。
 * @remarks 默认启用自动密钥轮换。
 */
export class KmsConstruct extends Construct {
  public readonly key: kms.Key;

  constructor(scope: Construct, id: string, props: KmsConstructProps = {}) {
    super(scope, id);
    const { alias = 'ai-agents-platform', enableKeyRotation = true } = props;

    this.key = new kms.Key(this, 'Key', {
      alias,
      enableKeyRotation,
      description: 'AI Agents Platform 数据加密主密钥',
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });
  }
}

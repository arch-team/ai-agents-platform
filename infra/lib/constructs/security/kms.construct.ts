import * as kms from 'aws-cdk-lib/aws-kms';
import { Construct } from 'constructs';
import { getRemovalPolicy, type EnvironmentName } from '../../config';

export interface KmsConstructProps {
  /** 环境名称 (dev, staging, prod) */
  readonly envName: EnvironmentName;
  /** KMS 密钥别名 @default 'ai-agents-platform' */
  readonly alias?: string;
  /** 是否启用自动密钥轮换 @default true */
  readonly enableKeyRotation?: boolean;
}

/**
 * KMS Construct - 创建平台加密主密钥。
 * @remarks 默认启用自动密钥轮换。Dev 环境使用 DESTROY 策略，其他环境使用 RETAIN 策略。
 */
export class KmsConstruct extends Construct {
  public readonly key: kms.Key;

  constructor(scope: Construct, id: string, props: KmsConstructProps) {
    super(scope, id);
    const { envName, alias = 'ai-agents-platform', enableKeyRotation = true } = props;

    this.key = new kms.Key(this, 'Key', {
      alias,
      enableKeyRotation,
      description: 'AI Agents Platform data encryption master key',
      removalPolicy: getRemovalPolicy(envName),
    });
  }
}

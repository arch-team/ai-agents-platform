import * as cdk from 'aws-cdk-lib';
import type { EnvironmentConfig, EnvironmentName } from './types';

/** 有效的环境名称集合 (v1.4: 移除 staging) */
const VALID_ENV_NAMES: ReadonlySet<string> = new Set<EnvironmentName>(['dev', 'prod']);

/**
 * 从 CDK Context 读取环境配置。
 * @remarks
 * - 环境名称通过 `-c env=dev` 传入，默认为 dev
 * - account/region 优先使用 cdk.json 配置，CDK_DEFAULT_* 仅在 cdk.json 未配置时作为 fallback
 * - 避免 shell 中 AWS_REGION 通过 CDK CLI 意外覆盖 cdk.json 中的目标区域
 */
export function getEnvironmentConfig(app: cdk.App): EnvironmentConfig {
  const envName = (app.node.tryGetContext('env') || 'dev') as string;

  if (!VALID_ENV_NAMES.has(envName)) {
    throw new Error(`无效的环境名称: ${envName}，支持的值: ${[...VALID_ENV_NAMES].join(', ')}`);
  }

  const environments = app.node.tryGetContext('environments');
  if (!environments || !environments[envName]) {
    throw new Error(`未找到环境配置: ${envName}`);
  }

  const config = environments[envName];
  const account = config.account || process.env.CDK_DEFAULT_ACCOUNT;
  const region = config.region || process.env.CDK_DEFAULT_REGION;

  if (!account || !region || !config.vpcCidr) {
    throw new Error(`环境 "${envName}" 配置不完整，需要 account, region, vpcCidr`);
  }

  if (account === '000000000000') {
    console.warn(
      `[警告] 环境 "${envName}" 使用了占位符账户 ID (000000000000)，请在 cdk.json 中配置真实的 AWS 账户 ID 或设置 CDK_DEFAULT_ACCOUNT 环境变量`,
    );
  }

  return {
    account,
    region,
    vpcCidr: config.vpcCidr,
    envName: envName as EnvironmentName,
    alertEmail: config.alertEmail,
    corsAllowedOrigins: config.corsAllowedOrigins,
    gatewayClientSecretArn: config.gatewayClientSecretArn,
    adminPasswordSecretArn: config.adminPasswordSecretArn,
  };
}

import * as cdk from 'aws-cdk-lib';

/** 环境配置接口 */
export interface EnvironmentConfig {
  readonly account: string;
  readonly region: string;
  readonly vpcCidr: string;
  readonly envName: string;
}

/**
 * 从 CDK Context 读取环境配置。
 * @remarks 环境名称通过 `-c env=dev` 传入，默认为 dev
 */
export function getEnvironmentConfig(app: cdk.App): EnvironmentConfig {
  const envName = app.node.tryGetContext('env') || 'dev';
  const environments = app.node.tryGetContext('environments');

  if (!environments || !environments[envName]) {
    throw new Error(`未找到环境配置: ${envName}`);
  }

  const config = environments[envName];

  // 检测占位符账户 ID，提醒用户配置真实值
  if (config.account === '000000000000') {
    console.warn(
      `[警告] 环境 "${envName}" 使用了占位符账户 ID (000000000000)，请在 cdk.json 中配置真实的 AWS 账户 ID`,
    );
  }

  return {
    account: config.account,
    region: config.region,
    vpcCidr: config.vpcCidr,
    envName,
  };
}

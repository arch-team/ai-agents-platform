import * as cdk from 'aws-cdk-lib';

/** 项目名称 */
export const PROJECT_NAME = 'ai-agents-platform';

/**
 * 获取必须标签。
 * @remarks 所有资源必须包含这些标签，用于成本追踪和资源管理
 */
export function getRequiredTags(envName: string): Record<string, string> {
  return {
    Project: PROJECT_NAME,
    Environment: envName,
    CostCenter: 'ai-platform',
    ManagedBy: 'cdk',
  };
}

/**
 * 根据环境名称获取 RemovalPolicy。
 * @remarks Dev 环境使用 DESTROY (便于迭代), Prod 使用 RETAIN, 其他使用 SNAPSHOT
 */
export function getRemovalPolicy(envName: string): cdk.RemovalPolicy {
  switch (envName) {
    case 'dev':
      return cdk.RemovalPolicy.DESTROY;
    case 'prod':
      return cdk.RemovalPolicy.RETAIN;
    default:
      return cdk.RemovalPolicy.SNAPSHOT;
  }
}

/**
 * 判断是否为 Dev 环境。
 * @remarks 用于条件配置，如删除保护、实例数量等
 */
export function isDev(envName: string): boolean {
  return envName === 'dev';
}

/**
 * 判断是否为 Prod 环境。
 * @remarks 用于条件配置，如多 AZ、高规格实例等
 */
export function isProd(envName: string): boolean {
  return envName === 'prod';
}

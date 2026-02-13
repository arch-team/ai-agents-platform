import * as cdk from 'aws-cdk-lib';
import type { EnvironmentName } from './types';

/** 项目名称 */
export const PROJECT_NAME = 'ai-agents-platform';

/**
 * 获取必须标签。
 * @remarks 所有资源必须包含这些标签，用于成本追踪和资源管理
 */
export function getRequiredTags(envName: EnvironmentName): Record<string, string> {
  return {
    Project: PROJECT_NAME,
    Environment: envName,
    CostCenter: 'ai-platform',
    ManagedBy: 'cdk',
  };
}

/**
 * 根据环境名称获取 RemovalPolicy。
 * @remarks Dev 环境使用 DESTROY (便于迭代), Prod 使用 RETAIN
 */
export function getRemovalPolicy(envName: EnvironmentName): cdk.RemovalPolicy {
  return envName === 'dev' ? cdk.RemovalPolicy.DESTROY : cdk.RemovalPolicy.RETAIN;
}

/**
 * 判断是否为 Dev 环境。
 * @remarks 用于条件配置，如删除保护、实例数量等
 */
export function isDev(envName: EnvironmentName): boolean {
  return envName === 'dev';
}

/**
 * 判断是否为 Prod 环境。
 * @remarks 用于条件配置，如多 AZ、高规格实例等
 */
export function isProd(envName: EnvironmentName): boolean {
  return envName === 'prod';
}

/** Bedrock 调用模型所需的 IAM actions (ComputeStack + AgentCoreStack 共享) */
export const BEDROCK_INVOKE_ACTIONS = [
  'bedrock:InvokeModel',
  'bedrock:InvokeModelWithResponseStream',
  'bedrock:ListInferenceProfiles',
] as const;

/**
 * 获取 Bedrock 调用权限的 IAM 资源 ARN 列表。
 * @remarks 限制到 foundation-model 和 inference-profile 资源
 */
export function getBedrockResourceArns(accountId: string): string[] {
  return [
    'arn:aws:bedrock:*::foundation-model/*',
    `arn:aws:bedrock:*:${accountId}:inference-profile/*`,
    `arn:aws:bedrock:*:${accountId}:application-inference-profile/*`,
  ];
}

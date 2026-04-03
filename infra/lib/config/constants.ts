import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import type { EnvironmentName } from './types';

/** 项目名称 */
export const PROJECT_NAME = 'ai-agents-platform';

/** 项目名下划线版本 (AWS 资源名不支持短横线时使用，如 AgentCore Runtime) */
export const PROJECT_NAME_UNDERSCORE = PROJECT_NAME.replace(/-/g, '_');

/** Stack 命名短前缀 (避免 CloudFormation 128 字符限制) */
export const STACK_PREFIX = 'ai-agents-plat';

/** 数据库默认端口 (Aurora MySQL) */
export const DB_PORT = 3306;

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

/**
 * 获取 CORS 允许的源列表。
 * @remarks 优先使用 cdk.json 中的 corsAllowedOrigins 配置; 未配置时使用默认值
 * @param envName - 环境名称
 * @param configuredOrigins - cdk.json 中配置的 CORS 源列表 (可选)
 */
export function getCorsAllowedOrigins(
  envName: EnvironmentName,
  configuredOrigins?: string[],
): string[] {
  if (configuredOrigins && configuredOrigins.length > 0) {
    return configuredOrigins;
  }
  // 回退默认值 — 建议将 CloudFront 域名迁移到 cdk.json environments 配置中
  if (envName === 'prod') {
    return ['https://d1dlap8e3g6mt5.cloudfront.net'];
  }
  return [
    'http://localhost:3000',
    'http://localhost:5173',
    'https://d2k7ovgb2e4af9.cloudfront.net',
  ];
}

/**
 * 获取 CloudWatch Logs 保留天数。
 * @remarks Prod: 3 个月; Dev: 1 周 (VPC Flow Log、ECS 日志等统一使用)
 */
export function getLogRetention(envName: EnvironmentName): logs.RetentionDays {
  return isProd(envName) ? logs.RetentionDays.THREE_MONTHS : logs.RetentionDays.ONE_WEEK;
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

/**
 * 创建 Bedrock InvokeModel IAM 策略声明。
 * @remarks ComputeStack 和 AgentCoreStack 共享，避免重复构造 PolicyStatement
 */
export function createBedrockInvokePolicy(accountId: string): iam.PolicyStatement {
  return new iam.PolicyStatement({
    actions: [...BEDROCK_INVOKE_ACTIONS],
    resources: getBedrockResourceArns(accountId),
  });
}

/** Bedrock 评估 Pipeline 所需的 IAM actions (M13 评估功能) */
export const BEDROCK_EVAL_ACTIONS = [
  'bedrock:CreateModelEvaluationJob',
  'bedrock:GetModelEvaluationJob',
  'bedrock:ListModelEvaluationJobs',
  'bedrock:StopModelEvaluationJob',
] as const;

/**
 * 获取 Bedrock 评估权限的 IAM 资源 ARN 列表。
 * @remarks 限制到 evaluation-job 资源
 */
export function getBedrockEvalResourceArns(accountId: string): string[] {
  return [`arn:aws:bedrock:*:${accountId}:evaluation-job/*`];
}

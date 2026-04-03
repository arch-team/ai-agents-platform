import * as cdk from 'aws-cdk-lib';

/** 支持的环境名称 (v1.4: 移除 staging，仅 Dev + Prod 两套环境) */
export type EnvironmentName = 'dev' | 'prod';

/**
 * 所有 Stack 的基础 Props 接口。
 * @remarks 统一提供 envName 属性，避免各 Stack 重复声明
 */
export interface BaseStackProps extends cdk.StackProps {
  /** 环境名称 (dev, prod) */
  readonly envName: EnvironmentName;
}

/** Agent 运行时模式: in_process (本地 CLI) / agentcore_runtime (AgentCore 托管) */
export type AgentRuntimeMode = 'in_process' | 'agentcore_runtime';

/** 有效的 Agent 运行时模式集合 */
export const VALID_AGENT_RUNTIME_MODES: readonly AgentRuntimeMode[] = [
  'in_process',
  'agentcore_runtime',
] as const;

/** 环境配置接口 */
export interface EnvironmentConfig {
  readonly account: string;
  readonly region: string;
  readonly vpcCidr: string;
  readonly envName: EnvironmentName;
  /** 告警通知邮箱地址 (可选) */
  readonly alertEmail?: string;
  /** CORS 允许的源列表 (可选, 覆盖 constants.ts 中的默认值) */
  readonly corsAllowedOrigins?: string[];
  /** Gateway Client Secret ARN (手动创建在 Secrets Manager) */
  readonly gatewayClientSecretArn?: string;
  /** 管理员密码 Secret ARN */
  readonly adminPasswordSecretArn?: string;
}

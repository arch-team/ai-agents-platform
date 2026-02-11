import * as cdk from 'aws-cdk-lib';

/**
 * 所有 Stack 的基础 Props 接口。
 * @remarks 统一提供 envName 属性，避免各 Stack 重复声明
 */
export interface BaseStackProps extends cdk.StackProps {
  /** 环境名称 (dev, staging, prod) */
  readonly envName: string;
}

/** 环境配置接口 */
export interface EnvironmentConfig {
  readonly account: string;
  readonly region: string;
  readonly vpcCidr: string;
  readonly envName: string;
}

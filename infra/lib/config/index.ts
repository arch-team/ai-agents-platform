// 配置模块桶导出
export {
  PROJECT_NAME,
  getRequiredTags,
  getRemovalPolicy,
  getLogRetention,
  isDev,
  isProd,
  getCorsAllowedOrigins,
  BEDROCK_INVOKE_ACTIONS,
  getBedrockResourceArns,
} from './constants';
export { getEnvironmentConfig } from './environments';
export type { BaseStackProps, EnvironmentConfig, EnvironmentName } from './types';

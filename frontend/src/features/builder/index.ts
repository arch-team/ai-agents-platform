// features/builder 公开 API

// UI 组件
export { BuilderChat } from './ui/BuilderChat';
export { BuilderPreview } from './ui/BuilderPreview';
export { BuilderActions } from './ui/BuilderActions';

// Store hooks
export {
  useBuilderStore,
  useBuilderSessionId,
  useBuilderStreamContent,
  useBuilderGeneratedConfig,
  useBuilderIsGenerating,
  useBuilderIsConfirming,
  useBuilderError,
  useBuilderActions,
} from './model/store';

// API hooks
export { useGetBuilderSession, builderKeys } from './api/queries';
export { useCreateBuilderSession, useConfirmBuilderSession } from './api/mutations';
export { useBuilderStream } from './api/stream';

// 类型
export type { BuilderSession, AgentConfig, BuilderStreamChunk } from './api/types';
export type { BuilderState } from './model/types';

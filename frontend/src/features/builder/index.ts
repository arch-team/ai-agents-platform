// features/builder 公开 API

// UI 组件
export { BuilderChat } from './ui/BuilderChat';
export { BuilderPreview } from './ui/BuilderPreview';
export { BuilderActions } from './ui/BuilderActions';
export { SkillCard } from './ui/SkillCard';
export { BuilderToolSelector } from './ui/ToolSelector';
export { TestSandbox } from './ui/TestSandbox';

// Store hooks
export {
  useBuilderStore,
  useBuilderSessionId,
  useBuilderStreamContent,
  useBuilderIsGenerating,
  useBuilderIsConfirming,
  useBuilderError,
  useBuilderActions,
  useBuilderPhase,
  useBuilderMessages,
  useBuilderBlueprint,
  useBuilderCreatedAgentId,
  useBuilderConfigOverrides,
} from './model/store';

// API hooks
export {
  useGetBuilderSession,
  useAvailableTools,
  useAvailableSkills,
  builderKeys,
} from './api/queries';
export {
  useCreateBuilderSession,
  useConfirmBuilderSession,
  useConfirmAndTest,
  useStartTesting,
  useGoLive,
  useCancelBuilderSession,
} from './api/mutations';
export { useBlueprintStream } from './api/stream';

// 类型
export type {
  BuilderSession,
  AgentConfig,
  BuilderStreamChunk,
  // V2
  BuilderPhase,
  GeneratedBlueprint,
  BlueprintStreamChunk,
  Persona,
  SkillDefinition,
  ToolBinding,
  MemoryConfig,
  Guardrail,
  ChatMessage,
  AvailableToolResponse,
  AvailableSkillResponse,
  SkillSummary,
  BlueprintConfigOverrides,
} from './api/types';
export type { BuilderState } from './model/types';

// Agent 相关常量 — 模型 ID 与 backend/src/shared/domain/constants.py 保持同步

/** 可选模型列表 (Bedrock cross-region inference model IDs) */
export const MODEL_OPTIONS = [
  {
    value: 'us.anthropic.claude-haiku-4-5-20251001-v1:0',
    label: 'Claude 4.5 Haiku (快速/低成本)',
  },
  {
    value: 'us.anthropic.claude-sonnet-4-6-20260819-v1:0',
    label: 'Claude 4.6 Sonnet (均衡)',
  },
  {
    value: 'us.anthropic.claude-opus-4-6-20260205-v1:0',
    label: 'Claude 4.6 Opus (最强)',
  },
] as const;

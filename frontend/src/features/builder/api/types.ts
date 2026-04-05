// Builder API 请求/响应类型

// ── V1 类型 (保留向后兼容) ──────────────────────────

export interface AgentConfig {
  name: string;
  description: string;
  system_prompt: string;
  model_id: string;
  temperature: number;
  max_tokens: number;
}

export interface BuilderStreamChunk {
  content?: string;
  config?: AgentConfig;
  done?: boolean;
  error?: string;
}

// ── V2 Blueprint 类型 ─────────────────────────────

export type BuilderPhase = 'input' | 'generating' | 'configure' | 'testing';

export interface Persona {
  role: string;
  background: string;
  tone?: string;
}

export interface SkillDefinition {
  name: string;
  trigger_description: string;
  steps: string[];
  rules: string[];
}

export interface ToolBinding {
  tool_id: number;
  display_name: string;
  usage_hint?: string;
}

export interface MemoryConfig {
  enabled: boolean;
  strategy: string;
  retain_fields: string[];
}

export interface Guardrail {
  rule: string;
  severity: 'warn' | 'block';
}

export interface GeneratedBlueprint {
  persona: Persona | null;
  skills: SkillDefinition[];
  tool_bindings: ToolBinding[];
  knowledge_base_ids: number[];
  memory_config: MemoryConfig | null;
  guardrails: Guardrail[];
}

export interface BlueprintStreamChunk {
  content?: string;
  blueprint?: GeneratedBlueprint;
  done?: boolean;
  error?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

// ── Session 类型 ───────────────────────────────────

export interface BuilderSession {
  id: number;
  user_id: number;
  prompt: string;
  status: 'pending' | 'generating' | 'confirmed' | 'cancelled';
  generated_config: AgentConfig | null;
  agent_name: string | null;
  created_agent_id: number | null;
  created_at: string;
  updated_at: string;
  // V2 字段
  messages: ChatMessage[];
  template_id: number | null;
  selected_skill_ids: number[];
  generated_blueprint: GeneratedBlueprint | null;
}

// ── 请求/响应类型 ──────────────────────────────────

export interface CreateBuilderSessionRequest {
  prompt: string;
  template_id?: number;
  selected_skill_ids?: number[];
}

export interface RefineBuilderRequest {
  message: string;
}

export interface ConfirmBuilderRequest {
  name_override?: string;
  auto_start_testing?: boolean;
}

export interface ConfirmBuilderSessionResponse {
  id: number;
  created_agent_id: number;
  status: 'confirmed';
  updated_at: string;
}

// ── 可用资源类型 ───────────────────────────────────

export interface AvailableToolResponse {
  id: number;
  name: string;
  description: string;
  tool_type: string;
}

export interface AvailableSkillResponse {
  id: number;
  name: string;
  description: string;
  category: string;
}

// Skill 摘要 — 用于 Builder UI 中展示可选 Skill 列表
export interface SkillSummary {
  id: number;
  name: string;
  description: string;
  category: string;
  trigger_description: string;
}

// Blueprint 配置覆盖 — 用户在预览面板手动调整的字段
export interface BlueprintConfigOverrides {
  tool_binding_ids?: number[];
  knowledge_base_ids?: number[];
  memory_enabled?: boolean;
  additional_guardrails?: string[];
}

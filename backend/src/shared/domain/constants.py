"""跨模块共享的领域常量。

Agent 和 Template 的 LLM 配置默认值集中定义在此，
各层（Domain / Application / API / Infrastructure）统一引用，避免魔术数字散落。
"""

# --- Bedrock 模型 ID 常量 (cross-region inference) ---
# Claude 4.5 Haiku (低成本、快速响应, 适合默认场景)
MODEL_CLAUDE_HAIKU_45: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
# Claude 4.6 Sonnet (均衡性能, 适合复杂任务)
MODEL_CLAUDE_SONNET_46: str = "us.anthropic.claude-sonnet-4-6-20260819-v1:0"
# Claude 4.6 Opus (最高能力, 1M 上下文窗口, 适合高复杂度 agentic 任务)
MODEL_CLAUDE_OPUS_46: str = "us.anthropic.claude-opus-4-6-20260205-v1:0"

# --- Agent 默认配置 ---
AGENT_DEFAULT_MODEL_ID: str = MODEL_CLAUDE_HAIKU_45
AGENT_DEFAULT_TEMPERATURE: float = 0.7
AGENT_DEFAULT_MAX_TOKENS: int = 2048
AGENT_DEFAULT_TOP_P: float = 1.0
AGENT_DEFAULT_RUNTIME_TYPE: str = "agent"

# --- Agent Teams 配置 ---
AGENT_DEFAULT_ENABLE_TEAMS: bool = False
AGENT_TEAMS_DEFAULT_MAX_TURNS: int = 200
AGENT_TEAMS_DEFAULT_TIMEOUT: int = 1800  # 30 分钟

# --- Template 默认配置 (temperature 与 Agent 相同, max_tokens 不同) ---
TEMPLATE_DEFAULT_MODEL_ID: str = MODEL_CLAUDE_HAIKU_45
TEMPLATE_DEFAULT_TEMPERATURE: float = 0.7
TEMPLATE_DEFAULT_MAX_TOKENS: int = 4096

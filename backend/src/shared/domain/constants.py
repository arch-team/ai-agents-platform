"""跨模块共享的领域常量。

Agent 和 Template 的 LLM 配置默认值集中定义在此，
各层（Domain / Application / API / Infrastructure）统一引用，避免魔术数字散落。
"""

# --- Agent 默认配置 ---
AGENT_DEFAULT_MODEL_ID: str = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
AGENT_DEFAULT_TEMPERATURE: float = 0.7
AGENT_DEFAULT_MAX_TOKENS: int = 2048
AGENT_DEFAULT_TOP_P: float = 1.0
AGENT_DEFAULT_RUNTIME_TYPE: str = "agent"

# --- Agent Teams 配置 ---
AGENT_DEFAULT_ENABLE_TEAMS: bool = False
AGENT_TEAMS_DEFAULT_MAX_TURNS: int = 200
AGENT_TEAMS_DEFAULT_TIMEOUT: int = 1800  # 30 分钟

# --- Template 默认配置 (temperature 与 Agent 相同, max_tokens 不同) ---
TEMPLATE_DEFAULT_TEMPERATURE: float = 0.7
TEMPLATE_DEFAULT_MAX_TOKENS: int = 4096

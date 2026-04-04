"""Blueprint 结构化输出解析器。

从 LLM 输出中解析 [SECTION]...[/SECTION] 结构化段。
纯函数，无外部依赖，属于 Application 层。
"""

import re
from dataclasses import dataclass, field


# ── 解析结果数据结构 ──


@dataclass(frozen=True)
class ParsedPersona:
    """解析后的 Agent 角色定义。"""

    role: str
    background: str
    tone: str = ""


@dataclass(frozen=True)
class ParsedSkill:
    """解析后的 Skill 定义。"""

    name: str
    trigger: str
    steps: tuple[str, ...] = ()
    rules: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParsedToolBinding:
    """解析后的工具绑定。"""

    tool_id: int
    display_name: str
    usage_hint: str = ""


@dataclass(frozen=True)
class ParsedGuardrail:
    """解析后的安全护栏规则。"""

    rule: str
    severity: str = "warn"


@dataclass
class ParsedBlueprint:
    """从 LLM 输出中解析出的完整 Blueprint。"""

    persona: ParsedPersona | None = None
    skills: list[ParsedSkill] = field(default_factory=list)
    tool_bindings: list[ParsedToolBinding] = field(default_factory=list)
    guardrails: list[ParsedGuardrail] = field(default_factory=list)


# ── 正则模式 ──

_SECTION_PATTERN = re.compile(
    r"\[(?P<tag>PERSONA|SKILL|TOOLS|GUARDRAILS)\]\s*\n(?P<body>.*?)\[/(?P=tag)\]",
    re.DOTALL,
)


# ── 解析器 ──


def parse_blueprint_output(text: str) -> ParsedBlueprint:
    """从 LLM 输出中解析结构化 Blueprint 段。

    支持多轮对话合并: 同类段后出现的覆盖前面的 (PERSONA), 或追加 (SKILL)。
    """
    blueprint = ParsedBlueprint()
    all_skills: list[ParsedSkill] = []

    for match in _SECTION_PATTERN.finditer(text):
        tag = match.group("tag")
        body = match.group("body").strip()

        if tag == "PERSONA":
            blueprint.persona = _parse_persona(body)
        elif tag == "SKILL":
            all_skills.append(_parse_skill(body))
        elif tag == "TOOLS":
            blueprint.tool_bindings = _parse_tools(body)
        elif tag == "GUARDRAILS":
            blueprint.guardrails = _parse_guardrails(body)

    blueprint.skills = all_skills
    return blueprint


def _parse_persona(body: str) -> ParsedPersona:
    """解析 PERSONA 段内容。"""
    fields = _parse_key_value_lines(body)
    return ParsedPersona(
        role=fields.get("role", "").strip(),
        background=fields.get("background", "").strip(),
        tone=fields.get("tone", "").strip(),
    )


def _parse_skill(body: str) -> ParsedSkill:
    """解析单个 SKILL 段内容。"""
    fields = _parse_key_value_lines(body)
    name = fields.get("name", "").strip()
    trigger = fields.get("trigger", "").strip()

    steps: list[str] = []
    rules: list[str] = []
    in_steps = False
    in_rules = False

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("steps:"):
            in_steps = True
            in_rules = False
            continue
        if stripped.lower().startswith("rules:"):
            in_rules = True
            in_steps = False
            continue

        if in_steps and re.match(r"^\d+\.\s", stripped):
            steps.append(stripped)
        elif in_rules and stripped.startswith("-"):
            rules.append(stripped.lstrip("- ").strip())

        if (
            re.match(r"^[a-z_]+:", stripped)
            and not stripped.startswith("-")
            and stripped.split(":")[0].strip() not in ("steps", "rules")
        ):
            in_steps = False
            in_rules = False

    return ParsedSkill(name=name, trigger=trigger, steps=tuple(steps), rules=tuple(rules))


_VALID_SEVERITIES = frozenset({"warn", "block"})


def _parse_tools(body: str) -> list[ParsedToolBinding]:
    """解析 TOOLS 段内容。"""
    bindings: list[ParsedToolBinding] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        content = stripped.lstrip("- ").strip()
        parts = _parse_comma_kv(content)
        # H4 修复: 验证 tool_id 合法性 (0 表示自定义工具, 允许)
        try:
            tool_id = int(parts.get("tool_id", "0"))
        except ValueError:
            continue
        if tool_id < 0:
            continue
        display_name = parts.get("display_name", "").strip()
        usage_hint = parts.get("usage_hint", "").strip()
        if display_name:
            bindings.append(ParsedToolBinding(tool_id=tool_id, display_name=display_name, usage_hint=usage_hint))
    return bindings


def _parse_guardrails(body: str) -> list[ParsedGuardrail]:
    """解析 GUARDRAILS 段内容。"""
    guardrails: list[ParsedGuardrail] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        content = stripped.lstrip("- ").strip()
        parts = _parse_comma_kv(content)
        rule_text = parts.get("rule", "").strip()
        severity = parts.get("severity", "warn").strip()
        # H4 修复: 验证 severity 枚举合法性
        if severity not in _VALID_SEVERITIES:
            severity = "warn"
        if rule_text:
            guardrails.append(ParsedGuardrail(rule=rule_text, severity=severity))
    return guardrails


def _parse_key_value_lines(text: str) -> dict[str, str]:
    """解析 key: value 格式的行 (仅提取顶层 key)。"""
    result: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if ":" in stripped and not stripped.startswith("-") and not re.match(r"^\d+\.", stripped):
            key, _, value = stripped.partition(":")
            key = key.strip().lower()
            if key and not key.startswith("["):
                result[key] = value.strip()
    return result


def _parse_comma_kv(text: str) -> dict[str, str]:
    """解析逗号分隔的 key: value 对 (如 'tool_id: 3, display_name: 订单查询')。"""
    result: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*:\s*([^,]+?)(?=,\s*\w+\s*:|$)", text):
        result[match.group(1).strip()] = match.group(2).strip()
    return result

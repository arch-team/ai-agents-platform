"""builder_prompts 单元测试 — 结构化输出解析 + 平台上下文格式化。"""

import pytest

from src.modules.builder.application.blueprint_parser import (
    ParsedBlueprint,
    parse_blueprint_output,
)
from src.modules.builder.infrastructure.external.builder_prompts import (
    build_system_prompt,
    format_platform_context,
)


# ── 解析器测试 ──


@pytest.mark.unit
class TestParseBlueprintOutput:
    """[SECTION]...[/SECTION] 结构化输出解析。"""

    def test_parse_full_output(self) -> None:
        """完整 4 段输出解析。"""
        text = """
好的，根据您的描述，我为您设计了以下 Agent：

[PERSONA]
role: 安克售后客服专员
background: 拥有安克全线产品知识，熟悉退换货政策和售后流程
tone: professional_friendly
[/PERSONA]

[SKILL]
name: return-processing
trigger: 客户提到退货、退款、换货
steps:
1. 查询订单状态 [tool: order-query-api]
2. 检查退货条件 [knowledge: 退货政策]
3. 生成退货单
rules:
- 先安抚情绪再处理
- 超过30天不予退货
[/SKILL]

[TOOLS]
- tool_id: 3, display_name: 订单查询, usage_hint: 客户提供订单号时调用
- tool_id: 5, display_name: 退货系统, usage_hint: 生成退货单时调用
[/TOOLS]

[GUARDRAILS]
- rule: 不得承诺超出政策的退款, severity: block
- rule: 涉及法律问题转人工, severity: block
- rule: 建议追加购买时需委婉, severity: warn
[/GUARDRAILS]

请确认以上配置，或者告诉我需要修改的地方。
"""
        result = parse_blueprint_output(text)

        assert isinstance(result, ParsedBlueprint)

        # Persona
        assert result.persona is not None
        assert result.persona.role == "安克售后客服专员"
        assert "安克全线产品知识" in result.persona.background
        assert result.persona.tone == "professional_friendly"

        # Skills
        assert len(result.skills) == 1
        assert result.skills[0].name == "return-processing"
        assert "退货" in result.skills[0].trigger
        assert len(result.skills[0].steps) >= 3
        assert len(result.skills[0].rules) >= 2

        # Tools
        assert len(result.tool_bindings) == 2
        assert result.tool_bindings[0].tool_id == 3
        assert result.tool_bindings[0].display_name == "订单查询"

        # Guardrails
        assert len(result.guardrails) == 3
        assert result.guardrails[0].severity == "block"
        assert result.guardrails[2].severity == "warn"

    def test_parse_partial_output_persona_only(self) -> None:
        """第一轮对话只有 PERSONA 段。"""
        text = """
[PERSONA]
role: 技术支持工程师
background: 负责产品技术问题排查
tone: patient_technical
[/PERSONA]

接下来请描述这个 Agent 需要处理的主要业务场景。
"""
        result = parse_blueprint_output(text)

        assert result.persona is not None
        assert result.persona.role == "技术支持工程师"
        assert len(result.skills) == 0
        assert len(result.tool_bindings) == 0
        assert len(result.guardrails) == 0

    def test_parse_multiple_skills(self) -> None:
        """多个 SKILL 段解析。"""
        text = """
[SKILL]
name: order-inquiry
trigger: 客户查询订单
steps:
1. 获取订单号
2. 查询订单状态
rules:
- 保护客户隐私
[/SKILL]

[SKILL]
name: complaint-handling
trigger: 客户投诉
steps:
1. 记录投诉内容
2. 分级处理
rules:
- 优先安抚
[/SKILL]
"""
        result = parse_blueprint_output(text)

        assert len(result.skills) == 2
        assert result.skills[0].name == "order-inquiry"
        assert result.skills[1].name == "complaint-handling"

    def test_parse_empty_text_returns_empty_blueprint(self) -> None:
        """空文本返回空 Blueprint。"""
        result = parse_blueprint_output("")
        assert result.persona is None
        assert len(result.skills) == 0

    def test_parse_no_sections_returns_empty_blueprint(self) -> None:
        """纯自然语言 (无标记) 返回空 Blueprint。"""
        text = "好的，让我们开始设计这个 Agent。请先描述您的业务场景。"
        result = parse_blueprint_output(text)
        assert result.persona is None
        assert len(result.skills) == 0

    def test_parse_tools_with_no_tool_id(self) -> None:
        """TOOLS 段中 tool_id 缺失时使用 0。"""
        text = """
[TOOLS]
- display_name: 自定义工具, usage_hint: 手动配置
[/TOOLS]
"""
        result = parse_blueprint_output(text)
        assert len(result.tool_bindings) == 1
        assert result.tool_bindings[0].tool_id == 0
        assert result.tool_bindings[0].display_name == "自定义工具"

    def test_parse_guardrails_default_severity(self) -> None:
        """GUARDRAILS 段中 severity 缺失时默认 warn。"""
        text = """
[GUARDRAILS]
- rule: 保持礼貌用语
[/GUARDRAILS]
"""
        result = parse_blueprint_output(text)
        assert len(result.guardrails) == 1
        assert result.guardrails[0].severity == "warn"

    def test_merge_conversation_history(self) -> None:
        """从多轮对话历史中提取最新的各段 (后出现的覆盖前面的)。"""
        round1 = """
[PERSONA]
role: 旧角色
background: 旧描述
tone: formal
[/PERSONA]
"""
        round2 = """
[PERSONA]
role: 新角色
background: 新描述
tone: casual
[/PERSONA]

[SKILL]
name: new-skill
trigger: 新触发
steps:
1. 第一步
rules:
- 新规则
[/SKILL]
"""
        # 解析合并后的文本 (模拟多轮对话)
        combined = round1 + "\n" + round2
        result = parse_blueprint_output(combined)

        # Persona 应该是最后一次出现的
        assert result.persona is not None
        assert result.persona.role == "新角色"
        assert len(result.skills) == 1


# ── 平台上下文格式化测试 ──


@pytest.mark.unit
class TestFormatPlatformContext:
    """平台上下文 → LLM prompt 文本。"""

    def test_format_with_tools_and_skills(self) -> None:
        tools = [
            {"id": 1, "name": "订单查询", "description": "查询客户订单状态"},
            {"id": 2, "name": "知识库搜索", "description": "搜索产品知识库"},
        ]
        skills = [
            {"id": 10, "name": "退货处理", "description": "处理客户退货请求", "category": "售后"},
        ]
        text = format_platform_context(tools, skills)

        assert "订单查询" in text
        assert "知识库搜索" in text
        assert "退货处理" in text
        assert "id: 1" in text or "ID: 1" in text

    def test_format_empty_context(self) -> None:
        text = format_platform_context([], [])
        assert "暂无" in text or "无可用" in text or len(text) > 0


# ── System Prompt 构建测试 ──


@pytest.mark.unit
class TestBuildSystemPrompt:
    """system prompt 构建。"""

    def test_system_prompt_contains_sop_phases(self) -> None:
        """system prompt 包含 4 个引导阶段的说明。"""
        prompt = build_system_prompt(platform_context_text="")

        # 应包含 4 个阶段的关键词
        assert "角色" in prompt or "PERSONA" in prompt
        assert "技能" in prompt or "SKILL" in prompt
        assert "工具" in prompt or "TOOLS" in prompt
        assert "护栏" in prompt or "GUARDRAILS" in prompt

    def test_system_prompt_includes_platform_context(self) -> None:
        """platform context 注入 system prompt。"""
        ctx = "平台可用工具: 订单查询(ID:1), 知识库(ID:2)"
        prompt = build_system_prompt(platform_context_text=ctx)

        assert "订单查询" in prompt
        assert "知识库" in prompt

    def test_system_prompt_includes_output_format(self) -> None:
        """system prompt 包含结构化输出格式说明。"""
        prompt = build_system_prompt(platform_context_text="")

        assert "[PERSONA]" in prompt
        assert "[/PERSONA]" in prompt
        assert "[SKILL]" in prompt
        assert "[GUARDRAILS]" in prompt

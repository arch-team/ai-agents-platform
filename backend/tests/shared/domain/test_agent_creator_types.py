"""agent_creator 共享类型测试。"""

import pytest

from src.shared.domain.interfaces.agent_creator import GuardrailData, GuardrailSeverity


class TestGuardrailSeverity:
    """GuardrailSeverity 枚举行为。"""

    def test_values(self) -> None:
        assert GuardrailSeverity.WARN == "warn"
        assert GuardrailSeverity.BLOCK == "block"

    def test_from_string(self) -> None:
        """StrEnum 支持从字符串构造（兼容现有 dict.get 调用）。"""
        assert GuardrailSeverity("warn") == GuardrailSeverity.WARN
        assert GuardrailSeverity("block") == GuardrailSeverity.BLOCK

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError):
            GuardrailSeverity("invalid")


class TestGuardrailDataWithEnum:
    """GuardrailData 使用 StrEnum severity。"""

    def test_default_severity(self) -> None:
        g = GuardrailData(rule="不可泄露密码")
        assert g.severity == GuardrailSeverity.WARN

    def test_string_severity_compat(self) -> None:
        """现有代码 GuardrailData(severity=g.get("severity", "warn")) 兼容性。"""
        g = GuardrailData(rule="禁止SQL注入", severity=GuardrailSeverity("warn"))
        assert g.severity == GuardrailSeverity.WARN

    def test_block_severity(self) -> None:
        g = GuardrailData(rule="禁止外部调用", severity=GuardrailSeverity.BLOCK)
        assert g.severity == "block"

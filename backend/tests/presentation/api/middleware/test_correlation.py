"""Correlation ID 中间件测试。"""

import pytest

from src.presentation.api.middleware.correlation import _sanitize_correlation_id


@pytest.mark.unit
class TestSanitizeCorrelationId:
    """Correlation ID 格式校验测试。"""

    def test_valid_uuid_passes(self) -> None:
        """标准 UUID 格式通过校验。"""
        result = _sanitize_correlation_id("550e8400-e29b-41d4-a716-446655440000")
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_alphanumeric_passes(self) -> None:
        """纯字母数字通过校验。"""
        result = _sanitize_correlation_id("abc123")
        assert result == "abc123"

    def test_alphanumeric_with_hyphens_passes(self) -> None:
        """带连字符的字母数字通过校验。"""
        result = _sanitize_correlation_id("req-abc-123")
        assert result == "req-abc-123"

    def test_none_generates_uuid(self) -> None:
        """None 时自动生成 UUID。"""
        result = _sanitize_correlation_id(None)
        assert len(result) == 36  # UUID 格式
        assert "-" in result

    def test_empty_string_generates_uuid(self) -> None:
        """空字符串时自动生成 UUID。"""
        result = _sanitize_correlation_id("")
        assert len(result) == 36

    def test_too_long_generates_uuid(self) -> None:
        """超过 128 字符时自动生成 UUID。"""
        long_id = "a" * 129
        result = _sanitize_correlation_id(long_id)
        assert result != long_id
        assert len(result) == 36

    def test_max_length_passes(self) -> None:
        """恰好 128 字符通过校验。"""
        max_id = "a" * 128
        result = _sanitize_correlation_id(max_id)
        assert result == max_id

    def test_special_chars_generates_uuid(self) -> None:
        """含特殊字符时自动生成 UUID。"""
        result = _sanitize_correlation_id("id<script>alert(1)</script>")
        assert "<script>" not in result
        assert len(result) == 36

    def test_newline_injection_generates_uuid(self) -> None:
        """含换行符注入时自动生成 UUID。"""
        result = _sanitize_correlation_id("id\r\nX-Injected-Header: value")
        assert "\r\n" not in result
        assert len(result) == 36

    def test_spaces_generates_uuid(self) -> None:
        """含空格时自动生成 UUID。"""
        result = _sanitize_correlation_id("id with spaces")
        assert len(result) == 36

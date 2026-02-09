"""通用 schemas 测试。"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.shared.api.schemas import ErrorResponse, PageRequest, PageResponse


@pytest.mark.unit
class TestErrorResponse:
    """ErrorResponse schema 测试。"""

    def test_create_error_response(self):
        """创建标准错误响应。"""
        # Arrange & Act
        resp = ErrorResponse(code="NOT_FOUND_USER", message="用户不存在")

        # Assert
        assert resp.code == "NOT_FOUND_USER"
        assert resp.message == "用户不存在"
        assert resp.details is None

    def test_create_error_response_with_details(self):
        """创建带 details 的错误响应。"""
        # Arrange & Act
        resp = ErrorResponse(
            code="INVALID_INPUT",
            message="验证失败",
            details={"field": "email", "reason": "格式错误"},
        )

        # Assert
        assert resp.details == {"field": "email", "reason": "格式错误"}

    def test_error_response_serialization(self):
        """ErrorResponse 序列化为 dict。"""
        # Arrange
        resp = ErrorResponse(code="INTERNAL_ERROR", message="服务器错误")

        # Act
        data = resp.model_dump()

        # Assert
        assert data["code"] == "INTERNAL_ERROR"
        assert data["message"] == "服务器错误"
        assert data["details"] is None


@pytest.mark.unit
class TestPageRequest:
    """PageRequest schema 测试。"""

    def test_default_values(self):
        """默认分页参数: page=1, page_size=20。"""
        # Arrange & Act
        req = PageRequest()

        # Assert
        assert req.page == 1
        assert req.page_size == 20

    def test_custom_values(self):
        """自定义分页参数。"""
        # Arrange & Act
        req = PageRequest(page=3, page_size=50)

        # Assert
        assert req.page == 3
        assert req.page_size == 50

    def test_page_size_max_100(self):
        """page_size 最大 100。"""
        # Arrange & Act & Assert
        with pytest.raises(PydanticValidationError):
            PageRequest(page_size=101)

    def test_page_min_1(self):
        """page 最小为 1。"""
        # Arrange & Act & Assert
        with pytest.raises(PydanticValidationError):
            PageRequest(page=0)

    def test_page_size_min_1(self):
        """page_size 最小为 1。"""
        # Arrange & Act & Assert
        with pytest.raises(PydanticValidationError):
            PageRequest(page_size=0)

    def test_offset_calculation(self):
        """offset 属性正确计算偏移量。"""
        # Arrange & Act
        req = PageRequest(page=3, page_size=20)

        # Assert — (3-1) * 20 = 40
        assert req.offset == 40

    def test_offset_first_page(self):
        """第一页 offset 为 0。"""
        # Arrange & Act
        req = PageRequest(page=1, page_size=20)

        # Assert
        assert req.offset == 0


@pytest.mark.unit
class TestPageResponse:
    """PageResponse schema 测试。"""

    def test_create_page_response(self):
        """创建分页响应。"""
        # Arrange & Act
        resp = PageResponse[str](
            items=["a", "b", "c"],
            total=10,
            page=1,
            page_size=3,
            total_pages=4,
        )

        # Assert
        assert resp.items == ["a", "b", "c"]
        assert resp.total == 10
        assert resp.page == 1
        assert resp.page_size == 3
        assert resp.total_pages == 4

    def test_empty_page_response(self):
        """空分页响应。"""
        # Arrange & Act
        resp = PageResponse[str](
            items=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=0,
        )

        # Assert
        assert resp.items == []
        assert resp.total == 0
        assert resp.total_pages == 0

    def test_page_response_serialization(self):
        """PageResponse 序列化为 dict。"""
        # Arrange
        resp = PageResponse[int](
            items=[1, 2, 3],
            total=100,
            page=2,
            page_size=3,
            total_pages=34,
        )

        # Act
        data = resp.model_dump()

        # Assert
        assert data["items"] == [1, 2, 3]
        assert data["total"] == 100
        assert data["page"] == 2

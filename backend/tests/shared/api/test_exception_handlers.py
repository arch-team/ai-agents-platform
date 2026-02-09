"""统一异常处理测试。"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.shared.api.exception_handlers import register_exception_handlers
from src.shared.domain.exceptions import (
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    ResourceQuotaExceededError,
    ValidationError,
)


def _create_test_app() -> FastAPI:
    """创建用于测试的 FastAPI 应用。"""
    app = FastAPI()
    register_exception_handlers(app)
    return app


@pytest.mark.unit
class TestExceptionHandlers:
    """统一异常处理测试。"""

    def setup_method(self):
        """每个测试前创建测试应用和客户端。"""
        self.app = _create_test_app()

    def test_entity_not_found_returns_404(self):
        """EntityNotFoundError 映射为 404。"""
        # Arrange
        @self.app.get("/test")
        def _endpoint():
            raise EntityNotFoundError(entity_type="User", entity_id=42)

        client = TestClient(self.app)

        # Act
        response = client.get("/test")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "NOT_FOUND_USER"
        assert "42" in data["message"]

    def test_duplicate_entity_returns_409(self):
        """DuplicateEntityError 映射为 409。"""
        # Arrange
        @self.app.get("/test")
        def _endpoint():
            raise DuplicateEntityError(entity_type="User", field="email", value="a@b.com")

        client = TestClient(self.app)

        # Act
        response = client.get("/test")

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "DUPLICATE_USER"

    def test_invalid_state_transition_returns_409(self):
        """InvalidStateTransitionError 映射为 409。"""
        # Arrange
        @self.app.get("/test")
        def _endpoint():
            raise InvalidStateTransitionError(
                entity_type="Agent",
                current_state="draft",
                target_state="archived",
            )

        client = TestClient(self.app)

        # Act
        response = client.get("/test")

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "INVALID_STATE_AGENT"

    def test_validation_error_returns_422(self):
        """ValidationError 映射为 422。"""
        # Arrange
        @self.app.get("/test")
        def _endpoint():
            raise ValidationError(message="名称不能为空", field="name")

        client = TestClient(self.app)

        # Act
        response = client.get("/test")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert data["code"] == "INVALID_INPUT"
        assert "名称不能为空" in data["message"]

    def test_resource_quota_exceeded_returns_429(self):
        """ResourceQuotaExceededError 映射为 429。"""
        # Arrange
        @self.app.get("/test")
        def _endpoint():
            raise ResourceQuotaExceededError(resource_type="agent", quota=10, requested=11)

        client = TestClient(self.app)

        # Act
        response = client.get("/test")

        # Assert
        assert response.status_code == 429
        data = response.json()
        assert "QUOTA_EXCEEDED" in data["code"]

    def test_generic_domain_error_returns_400(self):
        """未知 DomainError 子类映射为 400。"""
        # Arrange
        @self.app.get("/test")
        def _endpoint():
            raise DomainError(message="业务错误", code="CUSTOM_ERROR")

        client = TestClient(self.app)

        # Act
        response = client.get("/test")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "CUSTOM_ERROR"

    def test_unhandled_exception_returns_500(self):
        """未处理异常映射为 500, 不暴露内部信息。"""
        # Arrange
        @self.app.get("/test")
        def _endpoint():
            msg = "数据库连接失败"
            raise RuntimeError(msg)

        client = TestClient(self.app, raise_server_exceptions=False)

        # Act
        response = client.get("/test")

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert data["code"] == "INTERNAL_ERROR"
        # 不暴露内部异常信息
        assert "数据库连接失败" not in data["message"]

    def test_error_response_format(self):
        """错误响应符合 ErrorResponse 格式。"""
        # Arrange
        @self.app.get("/test")
        def _endpoint():
            raise EntityNotFoundError(entity_type="Agent", entity_id=1)

        client = TestClient(self.app)

        # Act
        response = client.get("/test")

        # Assert
        data = response.json()
        assert "code" in data
        assert "message" in data
        assert "details" in data

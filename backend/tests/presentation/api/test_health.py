"""Health check endpoints tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.presentation.api.main import create_app


@pytest.mark.unit
class TestHealthEndpoints:
    """Health check endpoint tests."""

    def setup_method(self) -> None:
        """Create test app and client."""
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_liveness_returns_ok(self) -> None:
        """GET /health returns status ok."""
        response = self.client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_readiness_without_db_returns_degraded(self) -> None:
        """GET /health/ready 数据库未初始化时返回 503 degraded。"""
        response = self.client.get("/health/ready")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert "checks" in data
        assert isinstance(data["checks"], dict)
        assert data["checks"]["database"] == "not_initialized"

    def test_readiness_response_has_correlation_id(self) -> None:
        """GET /health/ready 响应包含 X-Correlation-ID 头。"""
        response = self.client.get("/health/ready")

        assert "X-Correlation-ID" in response.headers

    def test_readiness_preserves_incoming_correlation_id(self) -> None:
        """请求携带 X-Correlation-ID 时，响应原样返回。"""
        test_id = "test-correlation-123"
        response = self.client.get(
            "/health/ready",
            headers={"X-Correlation-ID": test_id},
        )

        assert response.headers["X-Correlation-ID"] == test_id

    def test_liveness_has_correlation_id(self) -> None:
        """GET /health 响应包含 X-Correlation-ID 头。"""
        response = self.client.get("/health")

        assert "X-Correlation-ID" in response.headers

    @patch("src.presentation.api.routes.health.get_engine")
    def test_readiness_database_ok(self, mock_get_engine) -> None:
        """数据库连接正常时返回 200 ok。"""
        # Arrange — 模拟 engine.connect() 上下文管理器
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_engine = MagicMock()
        mock_engine.connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_get_engine.return_value = mock_engine

        # Act
        response = self.client.get("/health/ready")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["checks"]["database"] == "ok"

    @patch("src.presentation.api.routes.health.get_engine")
    def test_readiness_database_timeout(self, mock_get_engine) -> None:
        """数据库连接超时时返回 503 degraded。"""
        # Arrange
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__aenter__ = AsyncMock(side_effect=TimeoutError)
        mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_get_engine.return_value = mock_engine

        # Act
        response = self.client.get("/health/ready")

        # Assert
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["database"] == "timeout"

    @patch("src.presentation.api.routes.health.get_engine")
    def test_readiness_database_generic_error(self, mock_get_engine) -> None:
        """数据库连接其他异常时返回 503 degraded。"""
        # Arrange
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__aenter__ = AsyncMock(
            side_effect=ConnectionError("连接被拒绝"),
        )
        mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_get_engine.return_value = mock_engine

        # Act
        response = self.client.get("/health/ready")

        # Assert
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["database"] == "error"

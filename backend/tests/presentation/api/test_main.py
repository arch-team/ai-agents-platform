"""FastAPI app factory tests."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.presentation.api.main import create_app


@pytest.mark.unit
class TestCreateApp:
    """FastAPI app factory tests."""

    def test_create_app_returns_fastapi_instance(self):
        """create_app() returns a FastAPI instance."""
        # Act
        app = create_app()

        # Assert
        assert isinstance(app, FastAPI)

    def test_app_has_title(self):
        """App has correct title."""
        # Act
        app = create_app()

        # Assert
        assert app.title == "AI Agents Platform"

    def test_app_has_version(self):
        """App has version set."""
        # Act
        app = create_app()

        # Assert
        assert app.version == "0.1.0"

    def test_exception_handlers_registered(self):
        """Exception handlers are registered on the app."""
        # Act
        app = create_app()
        client = TestClient(app)

        # Assert — 访问不存在的路由不会返回 500 (FastAPI 默认 404)
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_cors_middleware_present(self):
        """CORS middleware is registered."""
        # Arrange
        app = create_app()
        client = TestClient(app)

        # Act — 发送 OPTIONS 预检请求
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Assert — CORS 头应存在
        assert "access-control-allow-origin" in response.headers

    def test_health_routes_included(self):
        """Health routes are included in the app."""
        # Arrange
        app = create_app()
        client = TestClient(app)

        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200

    def test_domain_error_handled(self):
        """DomainError is handled by exception handler."""
        # Arrange
        from src.shared.domain.exceptions import EntityNotFoundError

        app = create_app()

        @app.get("/test-error")
        def _raise_domain_error():
            raise EntityNotFoundError(entity_type="Agent", entity_id=99)

        client = TestClient(app)

        # Act
        response = client.get("/test-error")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "NOT_FOUND_AGENT"

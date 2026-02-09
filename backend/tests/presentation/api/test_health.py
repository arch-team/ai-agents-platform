"""Health check endpoints tests."""

import pytest
from fastapi.testclient import TestClient

from src.presentation.api.main import create_app


@pytest.mark.unit
class TestHealthEndpoints:
    """Health check endpoint tests."""

    def setup_method(self):
        """Create test app and client."""
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_liveness_returns_ok(self):
        """GET /health returns status ok."""
        # Act
        response = self.client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_readiness_returns_ok_with_checks(self):
        """GET /health/ready returns status and checks dict."""
        # Act
        response = self.client.get("/health/ready")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "checks" in data
        assert isinstance(data["checks"], dict)

    def test_readiness_status_field(self):
        """GET /health/ready status is ok when all checks pass."""
        # Act
        response = self.client.get("/health/ready")

        # Assert
        data = response.json()
        assert data["status"] in ("ok", "degraded")

"""SSO 端点集成测试。"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_sso_service
from src.modules.auth.application.services.sso_service import SsoService
from src.modules.auth.domain.exceptions import SsoAuthError, SsoNotConfiguredError
from src.modules.auth.domain.value_objects.sso_provider import SsoProvider
from src.presentation.api.main import create_app
from tests.modules.auth.conftest import make_user


@pytest.fixture
def mock_sso_service() -> MagicMock:
    return MagicMock(spec=SsoService)


@pytest.fixture
def client(mock_sso_service: MagicMock) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_sso_service] = lambda: mock_sso_service
    return TestClient(app)


@pytest.mark.integration
class TestSsoMetadataEndpoint:
    def test_returns_xml_metadata(self, client: TestClient, mock_sso_service: MagicMock) -> None:
        mock_sso_service.generate_saml_metadata.return_value = "<md:EntityDescriptor>...</md:EntityDescriptor>"

        response = client.get("/api/v1/auth/sso/metadata")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        assert "<md:EntityDescriptor>" in response.text
        mock_sso_service.generate_saml_metadata.assert_called_once()

    def test_returns_400_when_not_configured(self, client: TestClient, mock_sso_service: MagicMock) -> None:
        mock_sso_service.generate_saml_metadata.side_effect = SsoNotConfiguredError()

        response = client.get("/api/v1/auth/sso/metadata")

        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "SSO_NOT_CONFIGURED"


@pytest.mark.integration
class TestSsoInitEndpoint:
    def test_returns_redirect_url(self, client: TestClient, mock_sso_service: MagicMock) -> None:
        mock_sso_service.init_saml_login.return_value = (
            "https://idp.example.com/sso?SAMLRequest=encoded",
            "req-abc-123",
        )

        response = client.post(
            "/api/v1/auth/sso/init",
            json={"return_url": "https://app.example.com/dashboard"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["redirect_url"] == "https://idp.example.com/sso?SAMLRequest=encoded"
        assert data["request_id"] == "req-abc-123"

    def test_returns_400_when_not_configured(self, client: TestClient, mock_sso_service: MagicMock) -> None:
        mock_sso_service.init_saml_login.side_effect = SsoNotConfiguredError()

        response = client.post(
            "/api/v1/auth/sso/init",
            json={"return_url": "https://app.example.com"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "SSO_NOT_CONFIGURED"


@pytest.mark.integration
class TestSsoCallbackEndpoint:
    def test_returns_jwt_on_success(self, client: TestClient, mock_sso_service: MagicMock) -> None:
        user = make_user(user_id=1, sso_provider=SsoProvider.SAML, sso_subject="user@company.com")

        # mock process_saml_callback 为协程
        mock_sso_service.process_saml_callback = AsyncMock(return_value=user)
        mock_sso_service.create_token_for_user.return_value = "jwt-token-for-sso-user"

        response = client.post(
            "/api/v1/auth/sso/callback",
            data={"SAMLResponse": "base64-encoded-saml-response"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "jwt-token-for-sso-user"
        assert data["token_type"] == "bearer"

    def test_returns_401_on_saml_validation_failure(
        self, client: TestClient, mock_sso_service: MagicMock,
    ) -> None:
        mock_sso_service.process_saml_callback = AsyncMock(
            side_effect=SsoAuthError("SAML 验证失败: Signature mismatch"),
        )

        response = client.post(
            "/api/v1/auth/sso/callback",
            data={"SAMLResponse": "invalid-saml-response"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "SSO_AUTH_FAILED"

    def test_returns_400_when_not_configured(
        self, client: TestClient, mock_sso_service: MagicMock,
    ) -> None:
        mock_sso_service.process_saml_callback = AsyncMock(side_effect=SsoNotConfiguredError())

        response = client.post(
            "/api/v1/auth/sso/callback",
            data={"SAMLResponse": "any"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "SSO_NOT_CONFIGURED"

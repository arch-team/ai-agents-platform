"""SsoService 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.auth.application.services.sso_service import SsoService
from src.modules.auth.domain.exceptions import SsoAuthError, SsoNotConfiguredError
from src.modules.auth.domain.value_objects.sso_provider import SsoProvider
from tests.modules.auth.conftest import make_user


@pytest.mark.unit
class TestSsoServiceIsConfigured:
    def test_returns_true_when_configured(self, sso_service: SsoService) -> None:
        assert sso_service.is_configured is True

    def test_returns_false_when_unconfigured(self, unconfigured_sso_service: SsoService) -> None:
        assert unconfigured_sso_service.is_configured is False


@pytest.mark.unit
class TestSsoServiceInitSamlLogin:
    @patch("src.modules.auth.application.services.sso_service.OneLogin_Saml2_Auth")
    def test_returns_redirect_url_and_request_id(
        self,
        mock_auth_cls: MagicMock,
        sso_service: SsoService,
    ) -> None:
        # Arrange
        mock_auth = MagicMock()
        mock_auth.login.return_value = "https://idp.example.com/sso?SAMLRequest=xxx"
        mock_auth.get_last_request_id.return_value = "req-123"
        mock_auth_cls.return_value = mock_auth

        request_data: dict[str, object] = {
            "http_host": "localhost",
            "script_name": "/api/v1/auth/sso/init",
            "acs_url": "https://sp.example.com/callback",
        }

        # Act
        redirect_url, request_id = sso_service.init_saml_login(
            request_data,
            return_url="https://app.example.com/dashboard",
        )

        # Assert
        assert redirect_url == "https://idp.example.com/sso?SAMLRequest=xxx"
        assert request_id == "req-123"
        mock_auth.login.assert_called_once_with(return_to="https://app.example.com/dashboard")

    def test_raises_not_configured_when_no_config(self, unconfigured_sso_service: SsoService) -> None:
        with pytest.raises(SsoNotConfiguredError):
            unconfigured_sso_service.init_saml_login({}, return_url="https://app.example.com")


@pytest.mark.unit
class TestSsoServiceProcessSamlCallback:
    @pytest.mark.asyncio
    @patch("src.modules.auth.application.services.sso_service.OneLogin_Saml2_Auth")
    async def test_creates_new_user_on_first_login(
        self,
        mock_auth_cls: MagicMock,
        sso_service: SsoService,
        mock_user_repo: AsyncMock,
    ) -> None:
        # Arrange: SAML 验证成功
        mock_auth = MagicMock()
        mock_auth.get_errors.return_value = []
        mock_auth.is_authenticated.return_value = True
        mock_auth.get_nameid.return_value = "user@company.com"
        mock_auth.get_attributes.return_value = {"displayName": ["张三"]}
        mock_auth_cls.return_value = mock_auth

        # 用户不存在
        mock_user_repo.get_by_sso_subject.return_value = None
        created_user = make_user(
            user_id=10,
            email="user@company.com",
            name="张三",
            sso_provider=SsoProvider.SAML,
            sso_subject="user@company.com",
        )
        mock_user_repo.create.return_value = created_user

        # Act
        user = await sso_service.process_saml_callback(
            {"http_host": "localhost", "script_name": "/callback", "post_data": {}},
            acs_url="https://sp.example.com/callback",
        )

        # Assert
        assert user.id == 10
        assert user.sso_provider == SsoProvider.SAML
        mock_user_repo.get_by_sso_subject.assert_called_once_with("SAML", "user@company.com")
        mock_user_repo.create.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.modules.auth.application.services.sso_service.OneLogin_Saml2_Auth")
    async def test_returns_existing_user_on_subsequent_login(
        self,
        mock_auth_cls: MagicMock,
        sso_service: SsoService,
        mock_user_repo: AsyncMock,
    ) -> None:
        # Arrange: SAML 验证成功
        mock_auth = MagicMock()
        mock_auth.get_errors.return_value = []
        mock_auth.is_authenticated.return_value = True
        mock_auth.get_nameid.return_value = "user@company.com"
        mock_auth.get_attributes.return_value = {}
        mock_auth_cls.return_value = mock_auth

        # 用户已存在
        existing_user = make_user(
            user_id=5,
            email="user@company.com",
            name="已有用户",
            sso_provider=SsoProvider.SAML,
            sso_subject="user@company.com",
        )
        mock_user_repo.get_by_sso_subject.return_value = existing_user

        # Act
        user = await sso_service.process_saml_callback(
            {"http_host": "localhost", "script_name": "/callback", "post_data": {}},
            acs_url="https://sp.example.com/callback",
        )

        # Assert
        assert user.id == 5
        assert user.name == "已有用户"
        mock_user_repo.create.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.modules.auth.application.services.sso_service.OneLogin_Saml2_Auth")
    async def test_raises_sso_auth_error_on_validation_failure(
        self,
        mock_auth_cls: MagicMock,
        sso_service: SsoService,
    ) -> None:
        # Arrange: SAML 验证失败
        mock_auth = MagicMock()
        mock_auth.get_errors.return_value = ["invalid_response"]
        mock_auth.get_last_error_reason.return_value = "Signature validation failed"
        mock_auth_cls.return_value = mock_auth

        # Act & Assert
        with pytest.raises(SsoAuthError, match="SAML 验证失败"):
            await sso_service.process_saml_callback(
                {"http_host": "localhost", "script_name": "/callback", "post_data": {}},
                acs_url="https://sp.example.com/callback",
            )

    @pytest.mark.asyncio
    @patch("src.modules.auth.application.services.sso_service.OneLogin_Saml2_Auth")
    async def test_raises_sso_auth_error_when_not_authenticated(
        self,
        mock_auth_cls: MagicMock,
        sso_service: SsoService,
    ) -> None:
        # Arrange: 无错误但未认证
        mock_auth = MagicMock()
        mock_auth.get_errors.return_value = []
        mock_auth.is_authenticated.return_value = False
        mock_auth_cls.return_value = mock_auth

        # Act & Assert
        with pytest.raises(SsoAuthError, match="SAML 认证未通过"):
            await sso_service.process_saml_callback(
                {"http_host": "localhost", "script_name": "/callback", "post_data": {}},
                acs_url="https://sp.example.com/callback",
            )

    @pytest.mark.asyncio
    @patch("src.modules.auth.application.services.sso_service.OneLogin_Saml2_Auth")
    async def test_raises_sso_auth_error_when_missing_nameid(
        self,
        mock_auth_cls: MagicMock,
        sso_service: SsoService,
    ) -> None:
        # Arrange: 认证成功但无 NameID
        mock_auth = MagicMock()
        mock_auth.get_errors.return_value = []
        mock_auth.is_authenticated.return_value = True
        mock_auth.get_nameid.return_value = ""
        mock_auth_cls.return_value = mock_auth

        # Act & Assert
        with pytest.raises(SsoAuthError, match="缺少 NameID"):
            await sso_service.process_saml_callback(
                {"http_host": "localhost", "script_name": "/callback", "post_data": {}},
                acs_url="https://sp.example.com/callback",
            )

    @pytest.mark.asyncio
    async def test_raises_not_configured_error(self, unconfigured_sso_service: SsoService) -> None:
        with pytest.raises(SsoNotConfiguredError):
            await unconfigured_sso_service.process_saml_callback(
                {"http_host": "localhost", "script_name": "/callback", "post_data": {}},
                acs_url="https://sp.example.com/callback",
            )


@pytest.mark.unit
class TestSsoServiceCreateToken:
    def test_creates_jwt_for_user(self, sso_service: SsoService) -> None:
        user = make_user(user_id=42, sso_provider=SsoProvider.SAML)

        token = sso_service.create_token_for_user(user)

        assert isinstance(token, str)
        assert len(token) > 0


LDAP_PARAMS = {
    "server_url": "ldap://ldap.example.com:389",
    "bind_dn": "cn=admin,dc=example,dc=com",
    "bind_password": "secret",
    "base_dn": "dc=example,dc=com",
    "use_tls": False,
}


@pytest.mark.unit
class TestSsoServiceLdapConnectionTest:
    """LDAP 连接测试 — 通过 mock ldap3 验证三阶段逻辑。"""

    @patch("ldap3.Connection")
    @patch("ldap3.Server")
    def test_success_bind_and_search(self, mock_server_cls: MagicMock, mock_conn_cls: MagicMock) -> None:
        # Arrange
        mock_server = MagicMock()
        mock_server.info.vendor_name = "OpenLDAP"
        mock_server_cls.return_value = mock_server

        mock_conn = MagicMock()
        mock_conn.entries = [MagicMock()]  # 1 条搜索结果
        mock_conn_cls.return_value = mock_conn

        # Act
        result = SsoService._test_ldap_connection_sync(**LDAP_PARAMS)

        # Assert
        assert result.success is True
        assert "bind + search 均通过" in result.message
        assert result.details["server_url"] == "ldap://ldap.example.com:389"
        mock_conn.search.assert_called_once()
        mock_conn.unbind.assert_called_once()

    @patch("ldap3.Server")
    def test_server_unreachable(self, mock_server_cls: MagicMock) -> None:
        from ldap3.core.exceptions import LDAPSocketOpenError

        mock_server_cls.return_value = MagicMock()

        # Connection 抛出 socket 异常
        with patch(
            "ldap3.Connection",
            side_effect=LDAPSocketOpenError("unreachable"),
        ):
            result = SsoService._test_ldap_connection_sync(**LDAP_PARAMS)

        assert result.success is False
        assert "不可达" in result.message

    @patch("ldap3.Server")
    def test_bind_failure_bad_credentials(self, mock_server_cls: MagicMock) -> None:
        from ldap3.core.exceptions import LDAPBindError

        mock_server_cls.return_value = MagicMock()

        with patch(
            "ldap3.Connection",
            side_effect=LDAPBindError("invalid credentials"),
        ):
            result = SsoService._test_ldap_connection_sync(**LDAP_PARAMS)

        assert result.success is False
        assert "bind 失败" in result.message

    @patch("ldap3.Connection")
    @patch("ldap3.Server")
    def test_search_failure_permission_denied(self, mock_server_cls: MagicMock, mock_conn_cls: MagicMock) -> None:
        from ldap3.core.exceptions import LDAPOperationResult

        mock_server_cls.return_value = MagicMock()
        mock_conn = MagicMock()
        mock_conn.search.side_effect = LDAPOperationResult(result=50, description="insufficientAccessRights")
        mock_conn_cls.return_value = mock_conn

        result = SsoService._test_ldap_connection_sync(**LDAP_PARAMS)

        assert result.success is False
        assert "搜索失败" in result.message
        mock_conn.unbind.assert_called_once()

    @patch("ldap3.Connection")
    @patch("ldap3.Server")
    def test_tls_negotiation_failure(self, mock_server_cls: MagicMock, mock_conn_cls: MagicMock) -> None:
        from ldap3.core.exceptions import LDAPStartTLSError

        mock_server_cls.return_value = MagicMock()
        mock_conn = MagicMock()
        mock_conn.start_tls.side_effect = LDAPStartTLSError("TLS failed")
        mock_conn_cls.return_value = mock_conn

        result = SsoService._test_ldap_connection_sync(**{**LDAP_PARAMS, "use_tls": True})

        assert result.success is False
        assert "STARTTLS" in result.message
        mock_conn.unbind.assert_called_once()

    def test_details_always_contain_diagnostic_fields(self) -> None:
        """即使失败，details 也包含诊断字段。"""
        from ldap3.core.exceptions import LDAPSocketOpenError

        with patch("ldap3.Server"):
            with patch("ldap3.Connection", side_effect=LDAPSocketOpenError("fail")):
                result = SsoService._test_ldap_connection_sync(**LDAP_PARAMS)

        assert "server_url" in result.details
        assert "bind_dn" in result.details
        assert "base_dn" in result.details

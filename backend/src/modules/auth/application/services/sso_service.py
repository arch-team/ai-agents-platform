"""SSO 认证服务。"""

from dataclasses import dataclass

import structlog
from onelogin.saml2.auth import OneLogin_Saml2_Auth

from src.modules.auth.application.services.token_service import create_access_token
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.exceptions import SsoAuthError, SsoNotConfiguredError
from src.modules.auth.domain.repositories.user_repository import IUserRepository
from src.modules.auth.domain.value_objects.sso_provider import SsoProvider


logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class LdapTestResult:
    """LDAP 连接测试结果。"""

    success: bool
    message: str
    details: dict[str, str]


class SsoService:
    """SSO 认证服务，处理 SAML 登录流程。"""

    def __init__(
        self,
        repository: IUserRepository,
        *,
        sp_entity_id: str,
        sp_private_key: str,
        sp_certificate: str,
        idp_metadata_url: str,
        jwt_secret_key: str,
        jwt_algorithm: str = "HS256",
        jwt_expire_minutes: int = 30,
    ) -> None:
        self._repository = repository
        self._sp_entity_id = sp_entity_id
        self._sp_private_key = sp_private_key
        self._sp_certificate = sp_certificate
        self._idp_metadata_url = idp_metadata_url
        self._jwt_secret_key = jwt_secret_key
        self._jwt_algorithm = jwt_algorithm
        self._jwt_expire_minutes = jwt_expire_minutes

    @property
    def is_configured(self) -> bool:
        """检查 SAML 是否已配置。"""
        return bool(self._sp_entity_id and self._idp_metadata_url)

    def _require_configured(self) -> None:
        """检查 SAML 配置是否完整，未配置时抛出异常。"""
        if not self.is_configured:
            raise SsoNotConfiguredError

    def _get_saml_settings(self, acs_url: str, sls_url: str = "") -> dict[str, object]:
        """构建 python3-saml3 的配置字典。"""
        return {
            "strict": True,
            "debug": False,
            "sp": {
                "entityId": self._sp_entity_id,
                "assertionConsumerService": {
                    "url": acs_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "singleLogoutService": {
                    "url": sls_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "privateKey": self._sp_private_key,
                "x509cert": self._sp_certificate,
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            },
            "idp": {
                "entityId": "",
                "singleSignOnService": {
                    "url": "",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": "",
            },
        }

    def generate_saml_metadata(self, acs_url: str) -> str:
        """生成 SP metadata XML。

        Raises:
            SsoNotConfiguredError: SAML 未配置
        """
        self._require_configured()
        saml_settings = self._get_saml_settings(acs_url=acs_url)
        auth = OneLogin_Saml2_Auth({"http_host": "", "script_name": ""}, old_settings=saml_settings)
        metadata: str = auth.get_settings().get_sp_metadata()
        return metadata

    def init_saml_login(self, request_data: dict[str, object], return_url: str) -> tuple[str, str]:
        """发起 SAML 登录，返回 (redirect_url, request_id)。

        Raises:
            SsoNotConfiguredError: SAML 未配置
        """
        self._require_configured()
        acs_url = str(request_data.get("acs_url", ""))
        saml_settings = self._get_saml_settings(acs_url=acs_url)
        auth = OneLogin_Saml2_Auth(request_data, old_settings=saml_settings)
        redirect_url: str = auth.login(return_to=return_url)
        request_id: str = auth.get_last_request_id() or ""
        logger.info("sso_login_initiated", return_url=return_url)
        return redirect_url, request_id

    async def process_saml_callback(self, request_data: dict[str, object], acs_url: str) -> User:
        """处理 SAML Response 回调，验证并返回用户。

        验证 SAML Response → 提取 NameID → 查找或创建用户。

        Raises:
            SsoNotConfiguredError: SAML 未配置
            SsoAuthError: SAML Response 验证失败
        """
        self._require_configured()
        saml_settings = self._get_saml_settings(acs_url=acs_url)
        auth = OneLogin_Saml2_Auth(request_data, old_settings=saml_settings)
        auth.process_response()

        errors = auth.get_errors()
        if errors:
            error_reason = auth.get_last_error_reason() or ", ".join(errors)
            logger.warning("sso_saml_validation_failed", errors=errors, reason=error_reason)
            msg = f"SAML 验证失败: {error_reason}"
            raise SsoAuthError(msg)

        if not auth.is_authenticated():
            logger.warning("sso_saml_not_authenticated")
            msg = "SAML 认证未通过"
            raise SsoAuthError(msg)

        name_id: str = auth.get_nameid() or ""
        if not name_id:
            msg = "SAML Response 缺少 NameID"
            raise SsoAuthError(msg)

        # 从 SAML 属性中提取用户信息
        attributes = auth.get_attributes()
        email = name_id  # NameID 通常是邮箱
        display_name = ""
        if "displayName" in attributes:
            display_name = str(attributes["displayName"][0]) if attributes["displayName"] else ""
        elif "cn" in attributes:
            display_name = str(attributes["cn"][0]) if attributes["cn"] else ""

        if not display_name:
            # 使用邮箱前缀作为显示名
            display_name = email.split("@")[0]

        # 查找已有用户
        user = await self._repository.get_by_sso_subject(SsoProvider.SAML.value, name_id)
        if user is not None:
            logger.info("sso_user_found", user_id=user.id, sso_subject=name_id)
            return user

        # 创建新 SSO 用户 (密码设为随机不可用值, 因为 SSO 用户不使用密码登录)
        import secrets

        new_user = User(
            email=email,
            hashed_password=f"SSO_NO_PASSWORD_{secrets.token_hex(32)}",
            name=display_name,
            sso_provider=SsoProvider.SAML,
            sso_subject=name_id,
        )
        created = await self._repository.create(new_user)
        logger.info(
            "security_event",
            event_type="sso_user_created",
            user_id=created.id,
            sso_provider=SsoProvider.SAML.value,
        )
        return created

    def create_token_for_user(self, user: User) -> str:
        """为 SSO 用户创建 JWT access token。"""
        return create_access_token(
            subject=str(user.id),
            secret_key=self._jwt_secret_key,
            algorithm=self._jwt_algorithm,
            expire_minutes=self._jwt_expire_minutes,
            extra_claims={"role": user.role.value, "sso_provider": user.sso_provider.value},
        )

    async def test_ldap_connection(
        self,
        *,
        server_url: str,
        bind_dn: str,
        bind_password: str,
        base_dn: str,
        use_tls: bool = False,
    ) -> LdapTestResult:
        """测试 LDAP 服务器连接，返回测试结果。

        使用 asyncio.to_thread 包装 ldap3 同步调用。

        Raises:
            无 — 所有异常转为 LdapTestResult(success=False)
        """
        import asyncio

        return await asyncio.to_thread(
            self._test_ldap_connection_sync,
            server_url=server_url,
            bind_dn=bind_dn,
            bind_password=bind_password,
            base_dn=base_dn,
            use_tls=use_tls,
        )

    @staticmethod
    def _test_ldap_connection_sync(
        *,
        server_url: str,
        bind_dn: str,
        bind_password: str,
        base_dn: str,
        use_tls: bool = False,
    ) -> LdapTestResult:
        """同步 LDAP 连接测试: 连接 → bind → search（在线程池中执行）。"""
        import ssl

        from ldap3 import ALL, Connection, Server, Tls
        from ldap3.core.exceptions import LDAPException, LDAPSocketOpenError

        details: dict[str, str] = {
            "server_url": server_url,
            "bind_dn": bind_dn,
            "base_dn": base_dn,
            "use_tls": str(use_tls),
        }

        # 1. 创建 Server 连接
        try:
            tls_config = Tls(validate=ssl.CERT_NONE) if use_tls else None
            server = Server(server_url, use_ssl=server_url.startswith("ldaps://"), tls=tls_config, get_info=ALL)
        except LDAPException as e:
            return LdapTestResult(success=False, message=f"LDAP 服务器配置错误: {e}", details=details)

        # 2. Bind 认证
        try:
            conn = Connection(server, user=bind_dn, password=bind_password, auto_bind=True)
        except LDAPSocketOpenError:
            return LdapTestResult(success=False, message="LDAP 服务器不可达, 请检查 URL 和网络连通性", details=details)
        except LDAPException as e:
            return LdapTestResult(success=False, message=f"LDAP bind 失败(凭证错误或权限不足): {e}", details=details)

        # 3. STARTTLS (如配置)
        if use_tls and not server_url.startswith("ldaps://"):
            try:
                conn.start_tls()
            except LDAPException as e:
                conn.unbind()
                return LdapTestResult(success=False, message=f"STARTTLS 协商失败: {e}", details=details)

        # 4. Search 验证 (确认搜索权限)
        try:
            conn.search(search_base=base_dn, search_filter="(objectClass=*)", size_limit=1)
            entry_count = len(conn.entries)
            details["search_result"] = f"找到 {entry_count} 条目"
        except LDAPException as e:
            conn.unbind()
            return LdapTestResult(
                success=False,
                message=f"LDAP 搜索失败(权限不足或 base_dn 无效): {e}",
                details=details,
            )

        conn.unbind()
        details["server_info"] = str(server.info.vendor_name) if server.info and server.info.vendor_name else "未知"
        return LdapTestResult(success=True, message="LDAP 连接测试成功: bind + search 均通过", details=details)

"""SSO 认证 API 端点。"""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from src.modules.auth.api.dependencies import get_sso_service, require_role
from src.modules.auth.api.schemas.requests import LdapTestRequest, SsoInitRequest
from src.modules.auth.api.schemas.responses import LdapTestResponse, SsoInitResponse, TokenResponse
from src.modules.auth.application.services.sso_service import SsoService
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.exceptions import AuthenticationError
from src.modules.auth.domain.value_objects.role import Role
from src.shared.api.middleware.rate_limit import rate_limit
from src.shared.infrastructure.settings import Settings, get_settings


router = APIRouter(prefix="/api/v1/auth/sso", tags=["auth-sso"])

logger = structlog.get_logger(__name__)


def _build_saml_request_data(request: Request) -> dict[str, object]:
    """从 FastAPI Request 构建 python3-saml3 需要的请求数据。"""
    return {
        "http_host": request.headers.get("host", "localhost"),
        "script_name": str(request.url.path),
        "get_data": dict(request.query_params),
        "post_data": {},
    }


def _get_acs_url(request: Request) -> str:
    """获取 ACS (Assertion Consumer Service) URL。"""
    return str(request.url_for("sso_callback"))


@router.get("/metadata")
@rate_limit("10/minute")
async def sso_metadata(
    request: Request,
    service: Annotated[SsoService, Depends(get_sso_service)],
) -> Response:
    """返回 SP metadata XML。"""
    acs_url = _get_acs_url(request)
    metadata = service.generate_saml_metadata(acs_url=acs_url)
    return Response(content=metadata, media_type="application/xml")


@router.post("/init")
async def sso_init(
    request: Request,
    body: SsoInitRequest,
    service: Annotated[SsoService, Depends(get_sso_service)],
) -> SsoInitResponse:
    """发起 SSO 登录，返回 IdP 重定向 URL。"""
    request_data = _build_saml_request_data(request)
    request_data["acs_url"] = _get_acs_url(request)
    redirect_url, request_id = service.init_saml_login(request_data, return_url=body.return_url)
    return SsoInitResponse(redirect_url=redirect_url, request_id=request_id)


@router.post("/callback", name="sso_callback")
@rate_limit("10/minute")
async def sso_callback(
    request: Request,
    service: Annotated[SsoService, Depends(get_sso_service)],
) -> TokenResponse:
    """处理 SAML Response 回调，验证后签发 JWT。"""
    form_data = await request.form()
    request_data = _build_saml_request_data(request)
    request_data["post_data"] = dict(form_data)
    acs_url = _get_acs_url(request)

    user = await service.process_saml_callback(request_data, acs_url=acs_url)

    # [H-1] SSO 回调后检查用户是否已停用
    if not user.is_active:
        logger.warning(
            "security_event",
            event_type="sso_login_failed",
            user_id=user.id,
            reason="account_disabled",
        )
        msg = "账户已停用"
        raise AuthenticationError(msg)

    access_token = service.create_token_for_user(user)

    logger.info(
        "security_event",
        event_type="sso_login_success",
        user_id=user.id,
        sso_provider=user.sso_provider.value,
    )

    return TokenResponse(access_token=access_token)  # token_type 默认 "bearer"


@router.post("/ldap/test")
async def sso_ldap_test(
    body: LdapTestRequest,
    _current_user: Annotated[User, Depends(require_role(Role.ADMIN))],
    service: Annotated[SsoService, Depends(get_sso_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LdapTestResponse:
    """测试 LDAP 连接（仅 ADMIN）。请求体可选覆盖 Settings 默认值。"""
    server_url = body.server_url or settings.LDAP_SERVER_URL
    bind_dn = body.bind_dn or settings.LDAP_BIND_DN
    bind_password = body.bind_password or settings.LDAP_BIND_PASSWORD.get_secret_value()
    base_dn = body.base_dn or settings.LDAP_BASE_DN
    use_tls = body.use_tls if body.use_tls is not None else settings.LDAP_USE_TLS

    if not server_url:
        return LdapTestResponse(success=False, message="LDAP 服务器 URL 未配置")

    result = await service.test_ldap_connection(
        server_url=server_url,
        bind_dn=bind_dn,
        bind_password=bind_password,
        base_dn=base_dn,
        use_tls=use_tls,
    )

    logger.info("ldap_test_completed", success=result.success, server_url=server_url)
    return LdapTestResponse(success=result.success, message=result.message, details=result.details)

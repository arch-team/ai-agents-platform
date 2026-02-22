"""SSO 配置值对象。"""

from dataclasses import dataclass

from src.modules.auth.domain.value_objects.sso_provider import SsoProvider


@dataclass(frozen=True)
class SsoConfig:
    """SSO 配置（不可变值对象）。"""

    provider: SsoProvider
    saml_idp_metadata_url: str | None = None  # IdP metadata XML URL
    saml_sp_entity_id: str | None = None  # SP entity ID
    ldap_server_url: str | None = None  # 预留
    ldap_base_dn: str | None = None  # 预留

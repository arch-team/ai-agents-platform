"""SSO 提供者枚举。"""

from enum import StrEnum


class SsoProvider(StrEnum):
    """SSO 认证提供者类型。"""

    INTERNAL = "INTERNAL"  # 用户名密码
    SAML = "SAML"  # 企业 SAML 2.0
    LDAP = "LDAP"  # 企业 LDAP (预留)

"""JWT Token 服务。"""

from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError

from src.modules.auth.domain.exceptions import AuthenticationError


def create_access_token(
    subject: str,
    *,
    secret_key: str,
    algorithm: str,
    expire_minutes: int,
    extra_claims: dict[str, object] | None = None,
) -> str:
    """创建 JWT access token。"""
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=expire_minutes)
    payload: dict[str, object] = {"sub": subject, "exp": expire, "iat": now}
    if extra_claims:
        payload.update(extra_claims)
    return str(jwt.encode(payload, secret_key, algorithm=algorithm))


def decode_access_token(
    token: str,
    *,
    secret_key: str,
    algorithm: str,
) -> dict[str, object]:
    """解码并验证 JWT access token。

    Raises:
        AuthenticationError: token 无效或已过期
    """
    try:
        payload: dict[str, object] = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
        )
    except InvalidTokenError as e:
        msg = "无效的认证令牌"
        raise AuthenticationError(msg) from e
    return payload

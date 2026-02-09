"""JWT Token 服务。"""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from src.modules.auth.domain.exceptions import AuthenticationError


def create_access_token(
    subject: str,
    *,
    secret_key: str,
    algorithm: str,
    expire_minutes: int,
    extra_claims: dict[str, object] | None = None,
) -> str:
    """创建 JWT access token。

    Args:
        subject: token 主体 (通常是 user_id)
        secret_key: JWT 签名密钥
        algorithm: JWT 签名算法
        expire_minutes: token 过期时间 (分钟)
        extra_claims: 额外的 JWT claims

    """
    expire = datetime.now(UTC) + timedelta(minutes=expire_minutes)
    payload: dict[str, object] = {
        "sub": subject,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    result: str = jwt.encode(payload, secret_key, algorithm=algorithm)
    return result


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
    except JWTError as e:
        msg = "无效的认证令牌"
        raise AuthenticationError(msg) from e
    return payload

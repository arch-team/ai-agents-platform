"""密码哈希服务 - 直接使用 bcrypt 库。"""

import bcrypt


def hash_password(plain_password: str) -> str:
    """对明文密码进行 bcrypt 哈希。"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否匹配哈希值。"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )

"""用户应用服务。"""

import structlog

from src.modules.auth.application.dto.user_dto import (
    CreateUserDTO,
    LoginDTO,
    RefreshTokenDTO,
    TokenDTO,
    UserDTO,
)
from src.modules.auth.application.services.password_service import (
    hash_password,
    verify_password,
)
from src.modules.auth.application.services.token_service import create_access_token
from src.modules.auth.domain.entities.refresh_token import RefreshToken
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.exceptions import (
    AccountLockedError,
    AuthenticationError,
    InvalidRefreshTokenError,
    UserAlreadyExistsError,
)
from src.modules.auth.domain.repositories.refresh_token_repository import (
    IRefreshTokenRepository,
)
from src.modules.auth.domain.repositories.user_repository import IUserRepository


logger = structlog.get_logger(__name__)


class UserService:
    """用户业务服务，编排注册、登录等用例。"""

    def __init__(
        self,
        repository: IUserRepository,
        *,
        jwt_secret_key: str,
        jwt_algorithm: str = "HS256",
        jwt_expire_minutes: int = 30,
        max_login_attempts: int = 5,
        lockout_minutes: int = 30,
        refresh_token_repository: IRefreshTokenRepository | None = None,
        refresh_token_expire_days: int = 7,
    ) -> None:
        self._repository = repository
        self._jwt_secret_key = jwt_secret_key
        self._jwt_algorithm = jwt_algorithm
        self._jwt_expire_minutes = jwt_expire_minutes
        self._max_login_attempts = max_login_attempts
        self._lockout_minutes = lockout_minutes
        self._refresh_token_repository = refresh_token_repository
        self._refresh_token_expire_days = refresh_token_expire_days

    async def register(self, dto: CreateUserDTO) -> UserDTO:
        """注册新用户。

        Raises:
            UserAlreadyExistsError: 邮箱已被注册
        """
        existing = await self._repository.get_by_email(dto.email)
        if existing is not None:
            raise UserAlreadyExistsError(dto.email)

        user = User(
            email=dto.email,
            hashed_password=hash_password(dto.password),
            name=dto.name,
        )
        created = await self._repository.create(user)
        logger.info(
            "security_event",
            event_type="register_success",
            user_id=created.id,
        )
        return self._to_dto(created)

    async def login(self, dto: LoginDTO) -> TokenDTO:
        """用户登录，返回 JWT token + refresh token。

        Raises:
            AuthenticationError: 邮箱或密码错误
            AccountLockedError: 账户已锁定
        """
        user = await self._repository.get_by_email(dto.email)
        if user is None:
            logger.warning(
                "security_event",
                event_type="login_failed",
                reason="user_not_found",
            )
            msg = "邮箱或密码错误"
            raise AuthenticationError(msg)

        if not user.is_active:
            logger.warning(
                "security_event",
                event_type="login_failed",
                user_id=user.id,
                reason="account_disabled",
            )
            msg = "账户已停用"
            raise AuthenticationError(msg)

        # 检查账户锁定状态
        if user.is_locked:
            logger.warning(
                "security_event",
                event_type="login_failed",
                user_id=user.id,
                reason="account_locked",
            )
            raise AccountLockedError(locked_until=user.locked_until)  # type: ignore[arg-type]

        if not verify_password(dto.password, user.hashed_password):
            # 记录登录失败并持久化
            user.record_failed_login(
                max_attempts=self._max_login_attempts,
                lockout_minutes=self._lockout_minutes,
            )
            await self._repository.update(user)

            # 检查是否触发锁定
            if user.is_locked:
                logger.warning(
                    "security_event",
                    event_type="account_locked",
                    user_id=user.id,
                    failed_attempts=user.failed_login_count,
                )
            else:
                logger.warning(
                    "security_event",
                    event_type="login_failed",
                    user_id=user.id,
                    reason="invalid_password",
                    failed_attempts=user.failed_login_count,
                )
            msg = "邮箱或密码错误"
            raise AuthenticationError(msg)

        # 登录成功, 重置失败计数
        if user.failed_login_count > 0:
            user.reset_failed_logins()
            await self._repository.update(user)

        access_token = create_access_token(
            subject=str(user.id),
            secret_key=self._jwt_secret_key,
            algorithm=self._jwt_algorithm,
            expire_minutes=self._jwt_expire_minutes,
            extra_claims={"role": user.role.value},
        )

        # 签发 Refresh Token
        refresh_token_str = ""
        if self._refresh_token_repository is not None:
            refresh_token = RefreshToken(user_id=user.id or 0)
            created_rt = await self._refresh_token_repository.create(refresh_token)
            refresh_token_str = created_rt.token

        logger.info(
            "security_event",
            event_type="login_success",
            user_id=user.id,
            token_type="access_token+refresh_token" if refresh_token_str else "access_token",
        )

        return TokenDTO(access_token=access_token, refresh_token=refresh_token_str)

    async def refresh_access_token(self, dto: RefreshTokenDTO) -> TokenDTO:
        """使用 Refresh Token 换发新的 Access Token。

        Raises:
            InvalidRefreshTokenError: Refresh Token 无效或已过期
        """
        if self._refresh_token_repository is None:
            msg = "Refresh Token 功能未启用"
            raise InvalidRefreshTokenError(msg)

        rt = await self._refresh_token_repository.get_by_token(dto.refresh_token)
        if rt is None or not rt.is_valid:
            logger.warning(
                "security_event",
                event_type="token_refresh_failed",
                reason="invalid_or_expired",
            )
            raise InvalidRefreshTokenError

        # 检查用户状态
        user = await self._repository.get_by_id(rt.user_id)
        if user is None or not user.is_active:
            # 用户不存在或已停用, 撤销 Token
            rt.revoke()
            await self._refresh_token_repository.update(rt)
            logger.warning(
                "security_event",
                event_type="token_refresh_failed",
                user_id=rt.user_id,
                reason="account_disabled",
            )
            msg = "账户已停用"
            raise AuthenticationError(msg)

        # Refresh Token Rotation: 撤销旧 Token, 签发新 Token
        rt.revoke()
        await self._refresh_token_repository.update(rt)

        new_rt = RefreshToken(
            user_id=user.id or 0,
        )
        created_rt = await self._refresh_token_repository.create(new_rt)

        access_token = create_access_token(
            subject=str(user.id),
            secret_key=self._jwt_secret_key,
            algorithm=self._jwt_algorithm,
            expire_minutes=self._jwt_expire_minutes,
            extra_claims={"role": user.role.value},
        )
        logger.info(
            "security_event",
            event_type="token_refreshed",
            user_id=user.id,
        )
        return TokenDTO(access_token=access_token, refresh_token=created_rt.token)

    async def logout(self, refresh_token: str) -> bool:
        """撤销 Refresh Token（登出）。"""
        if self._refresh_token_repository is None:
            return False
        result = await self._refresh_token_repository.revoke_by_token(refresh_token)
        logger.info(
            "security_event",
            event_type="logout",
            token_revoked=result,
        )
        return result

    async def revoke_user_tokens(self, user_id: int) -> int:
        """撤销用户所有 Refresh Token（用于停用用户或角色变更）。"""
        if self._refresh_token_repository is None:
            return 0
        count = await self._refresh_token_repository.revoke_by_user_id(user_id)
        logger.info(
            "security_event",
            event_type="tokens_revoked",
            target_user_id=user_id,
            revoked_count=count,
        )
        return count

    async def get_user(self, user_id: int) -> UserDTO | None:
        """根据 ID 获取用户信息。"""
        user = await self._repository.get_by_id(user_id)
        if user is None:
            return None
        return self._to_dto(user)

    @staticmethod
    def _to_dto(user: User) -> UserDTO:
        return UserDTO(
            id=user.id or 0,
            email=str(user.email),
            name=user.name,
            role=user.role.value,
            is_active=user.is_active,
        )

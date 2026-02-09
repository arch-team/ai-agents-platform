"""用户应用服务。"""

from src.modules.auth.application.dto.user_dto import (
    CreateUserDTO,
    LoginDTO,
    TokenDTO,
    UserDTO,
)
from src.modules.auth.application.services.password_service import (
    hash_password,
    verify_password,
)
from src.modules.auth.application.services.token_service import create_access_token
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.exceptions import (
    AuthenticationError,
    UserAlreadyExistsError,
)
from src.modules.auth.domain.repositories.user_repository import IUserRepository


class UserService:
    """用户业务服务，编排注册、登录等用例。"""

    def __init__(
        self,
        repository: IUserRepository,
        *,
        jwt_secret_key: str,
        jwt_algorithm: str = "HS256",
        jwt_expire_minutes: int = 30,
    ) -> None:
        self._repository = repository
        self._jwt_secret_key = jwt_secret_key
        self._jwt_algorithm = jwt_algorithm
        self._jwt_expire_minutes = jwt_expire_minutes

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
        return self._to_dto(created)

    async def login(self, dto: LoginDTO) -> TokenDTO:
        """用户登录，返回 JWT token。

        Raises:
            AuthenticationError: 邮箱或密码错误
        """
        user = await self._repository.get_by_email(dto.email)
        if user is None:
            msg = "邮箱或密码错误"
            raise AuthenticationError(msg)

        if not user.is_active:
            msg = "账户已停用"
            raise AuthenticationError(msg)

        if not verify_password(dto.password, user.hashed_password):
            msg = "邮箱或密码错误"
            raise AuthenticationError(msg)

        token = create_access_token(
            subject=str(user.id),
            secret_key=self._jwt_secret_key,
            algorithm=self._jwt_algorithm,
            expire_minutes=self._jwt_expire_minutes,
            extra_claims={"role": user.role.value},
        )
        return TokenDTO(access_token=token)

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

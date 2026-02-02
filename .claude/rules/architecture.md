# 架构规范 (Architecture Standards)

本文档定义 Python 后端项目的架构规范，采用 Clean Architecture 分层架构。

---

## Clean Architecture 概述

### 核心原则

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│                 (FastAPI, Pydantic Schemas)                  │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                      │
│          (SQLAlchemy, boto3, HTTP Clients, Config)          │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                         │
│              (Use Cases, DTOs, Interfaces)                   │
├─────────────────────────────────────────────────────────────┤
│                      Domain Layer                            │
│      (Entities, Value Objects, Domain Services, Events)      │
└─────────────────────────────────────────────────────────────┘

        ↑ 依赖方向：外层依赖内层，内层不知道外层存在
```

### 依赖规则 (The Dependency Rule)

| 层级 | 可以依赖 | 禁止依赖 |
|------|---------|---------|
| **Domain** | 无 (纯 Python) | FastAPI, Pydantic, SQLAlchemy, boto3 |
| **Application** | Domain | FastAPI, SQLAlchemy, boto3 |
| **Infrastructure** | Domain, Application | - |
| **Presentation** | Application, Domain | Infrastructure (通过 DI) |

---

## 项目结构

### 完整目录结构

```
src/
├── __init__.py
├── domain/                    # 领域层
│   ├── __init__.py
│   ├── entities/              # 实体 (有身份标识的对象)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── training_job.py
│   ├── value_objects/         # 值对象 (不可变，无身份标识)
│   │   ├── __init__.py
│   │   ├── email.py
│   │   ├── job_status.py
│   │   └── s3_uri.py
│   ├── events/                # 领域事件
│   │   ├── __init__.py
│   │   └── job_events.py
│   ├── services/              # 领域服务
│   │   ├── __init__.py
│   │   └── job_scheduler.py
│   ├── repositories/          # 仓储接口 (抽象基类)
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   └── job_repository.py
│   └── exceptions.py          # 领域异常
│
├── application/               # 应用层
│   ├── __init__.py
│   ├── use_cases/             # 用例/应用服务
│   │   ├── __init__.py
│   │   ├── user/
│   │   │   ├── __init__.py
│   │   │   ├── create_user.py
│   │   │   └── get_user.py
│   │   └── training/
│   │       ├── __init__.py
│   │       ├── create_job.py
│   │       └── get_job_status.py
│   ├── dto/                   # 数据传输对象
│   │   ├── __init__.py
│   │   ├── user_dto.py
│   │   └── job_dto.py
│   ├── interfaces/            # 端口接口 (外部服务抽象)
│   │   ├── __init__.py
│   │   ├── email_service.py
│   │   └── storage_service.py
│   └── exceptions.py          # 应用层异常
│
├── infrastructure/            # 基础设施层
│   ├── __init__.py
│   ├── database/              # 数据库相关
│   │   ├── __init__.py
│   │   ├── connection.py      # 数据库连接
│   │   ├── models/            # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   ├── user_model.py
│   │   │   └── job_model.py
│   │   └── repositories/      # 仓储实现
│   │       ├── __init__.py
│   │       ├── sqlalchemy_user_repository.py
│   │       └── sqlalchemy_job_repository.py
│   ├── external/              # 外部服务适配器
│   │   ├── __init__.py
│   │   ├── aws/               # AWS 服务
│   │   │   ├── __init__.py
│   │   │   ├── sagemaker_adapter.py
│   │   │   └── s3_adapter.py
│   │   └── email/             # 邮件服务
│   │       ├── __init__.py
│   │       └── ses_email_service.py
│   └── config/                # 配置管理
│       ├── __init__.py
│       └── settings.py
│
└── presentation/              # 表现层
    ├── __init__.py
    ├── api/                   # FastAPI 应用
    │   ├── __init__.py
    │   ├── main.py            # 应用入口
    │   ├── routes/            # 路由定义
    │   │   ├── __init__.py
    │   │   ├── user_routes.py
    │   │   └── job_routes.py
    │   ├── dependencies/      # 依赖注入
    │   │   ├── __init__.py
    │   │   └── container.py
    │   └── middleware/        # 中间件
    │       ├── __init__.py
    │       └── error_handler.py
    └── schemas/               # Pydantic 模型
        ├── __init__.py
        ├── user_schemas.py
        └── job_schemas.py
```

---

## 领域层 (Domain Layer)

### 实体 (Entities)

实体是具有唯一身份标识的对象，身份在生命周期内保持不变。

```python
# src/domain/entities/user.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Self
from uuid import UUID, uuid4

from src.domain.value_objects import Email
from src.domain.exceptions import ValidationError


@dataclass
class User:
    """用户实体。

    Attributes:
        id: 用户唯一标识
        name: 用户名称
        email: 用户邮箱
        is_active: 是否激活
        created_at: 创建时间
    """

    name: str
    email: Email
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """初始化后验证。"""
        self._validate()

    def _validate(self) -> None:
        """验证实体数据。"""
        if not self.name or not self.name.strip():
            raise ValidationError("名称不能为空")
        if len(self.name) > 100:
            raise ValidationError("名称不能超过 100 个字符")

    def deactivate(self) -> None:
        """停用用户。"""
        self.is_active = False

    def activate(self) -> None:
        """激活用户。"""
        self.is_active = True

    def update_email(self, new_email: Email) -> None:
        """更新邮箱。"""
        self.email = new_email

    def __eq__(self, other: object) -> bool:
        """实体相等性基于 ID。"""
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """实体哈希基于 ID。"""
        return hash(self.id)
```

### 值对象 (Value Objects)

值对象是不可变的，没有身份标识，相等性基于属性值。

```python
# src/domain/value_objects/email.py

from dataclasses import dataclass
import re

from src.domain.exceptions import ValidationError


@dataclass(frozen=True)  # frozen=True 确保不可变
class Email:
    """邮箱值对象。

    Attributes:
        value: 邮箱地址字符串
    """

    value: str

    _EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    def __post_init__(self) -> None:
        """初始化后验证。"""
        if not self._EMAIL_PATTERN.match(self.value):
            raise ValidationError(f"无效的邮箱格式: {self.value}")

    def __str__(self) -> str:
        """返回邮箱字符串。"""
        return self.value

    @property
    def domain(self) -> str:
        """获取邮箱域名。"""
        return self.value.split("@")[1]

    @property
    def local_part(self) -> str:
        """获取邮箱本地部分。"""
        return self.value.split("@")[0]
```

### 仓储接口 (Repository Interfaces)

仓储接口定义在领域层，实现在基础设施层。

```python
# src/domain/repositories/user_repository.py

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import User
from src.domain.value_objects import Email


class UserRepository(ABC):
    """用户仓储接口。

    定义用户持久化操作的抽象接口。
    """

    @abstractmethod
    def save(self, user: User) -> User:
        """保存用户。

        Args:
            user: 要保存的用户实体

        Returns:
            保存后的用户实体
        """
        ...

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None:
        """根据 ID 获取用户。

        Args:
            user_id: 用户 ID

        Returns:
            用户实体，如果不存在则返回 None
        """
        ...

    @abstractmethod
    def get_by_email(self, email: Email) -> User | None:
        """根据邮箱获取用户。

        Args:
            email: 邮箱值对象

        Returns:
            用户实体，如果不存在则返回 None
        """
        ...

    @abstractmethod
    def delete(self, user_id: UUID) -> bool:
        """删除用户。

        Args:
            user_id: 用户 ID

        Returns:
            是否删除成功
        """
        ...
```

---

## 应用层 (Application Layer)

### 用例 (Use Cases)

用例封装业务逻辑，协调领域对象完成任务。

```python
# src/application/use_cases/user/create_user.py

from dataclasses import dataclass

from src.domain.entities import User
from src.domain.value_objects import Email
from src.domain.repositories import UserRepository
from src.application.dto import CreateUserDTO, UserResponseDTO
from src.application.interfaces import EmailService
from src.application.exceptions import DuplicateEmailError


@dataclass
class CreateUserUseCase:
    """创建用户用例。

    协调领域对象和基础设施服务完成用户创建。

    Attributes:
        user_repository: 用户仓储接口
        email_service: 邮件服务接口
    """

    user_repository: UserRepository
    email_service: EmailService

    def execute(self, dto: CreateUserDTO) -> UserResponseDTO:
        """执行用例。

        Args:
            dto: 创建用户数据传输对象

        Returns:
            用户响应数据传输对象

        Raises:
            DuplicateEmailError: 当邮箱已存在时
        """
        # 1. 验证邮箱唯一性
        email = Email(dto.email)
        existing_user = self.user_repository.get_by_email(email)
        if existing_user:
            raise DuplicateEmailError(f"邮箱 {dto.email} 已被注册")

        # 2. 创建用户实体
        user = User(name=dto.name, email=email)

        # 3. 保存用户
        saved_user = self.user_repository.save(user)

        # 4. 发送欢迎邮件
        self.email_service.send_welcome_email(str(saved_user.email))

        # 5. 返回响应
        return UserResponseDTO.from_entity(saved_user)
```

### 数据传输对象 (DTOs)

DTO 用于层之间的数据传输，不包含业务逻辑。

```python
# src/application/dto/user_dto.py

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.entities import User


@dataclass(frozen=True)
class CreateUserDTO:
    """创建用户请求 DTO。"""

    name: str
    email: str


@dataclass(frozen=True)
class UpdateUserDTO:
    """更新用户请求 DTO。"""

    name: str | None = None
    email: str | None = None


@dataclass(frozen=True)
class UserResponseDTO:
    """用户响应 DTO。"""

    id: UUID
    name: str
    email: str
    is_active: bool
    created_at: datetime

    @classmethod
    def from_entity(cls, user: User) -> "UserResponseDTO":
        """从实体创建 DTO。"""
        return cls(
            id=user.id,
            name=user.name,
            email=str(user.email),
            is_active=user.is_active,
            created_at=user.created_at,
        )
```

---

## 基础设施层 (Infrastructure Layer)

### 仓储实现

```python
# src/infrastructure/database/repositories/sqlalchemy_user_repository.py

from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.entities import User
from src.domain.value_objects import Email
from src.domain.repositories import UserRepository
from src.infrastructure.database.models import UserModel


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy 用户仓储实现。

    Attributes:
        session: SQLAlchemy 数据库会话
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, user: User) -> User:
        """保存用户到数据库。"""
        model = UserModel.from_entity(user)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return model.to_entity()

    def get_by_id(self, user_id: UUID) -> User | None:
        """根据 ID 从数据库获取用户。"""
        model = self._session.query(UserModel).filter(
            UserModel.id == user_id
        ).first()
        return model.to_entity() if model else None

    def get_by_email(self, email: Email) -> User | None:
        """根据邮箱从数据库获取用户。"""
        model = self._session.query(UserModel).filter(
            UserModel.email == str(email)
        ).first()
        return model.to_entity() if model else None

    def delete(self, user_id: UUID) -> bool:
        """从数据库删除用户。"""
        result = self._session.query(UserModel).filter(
            UserModel.id == user_id
        ).delete()
        self._session.commit()
        return result > 0
```

### 外部服务适配器

```python
# src/infrastructure/external/aws/s3_adapter.py

from pathlib import Path

import boto3
from botocore.config import Config

from src.application.interfaces import StorageService
from src.domain.value_objects import S3Uri


class S3StorageAdapter(StorageService):
    """S3 存储适配器。

    实现存储服务接口，使用 AWS S3 作为后端存储。
    """

    def __init__(self, region_name: str = "us-west-2") -> None:
        config = Config(
            retries={"max_attempts": 3, "mode": "adaptive"}
        )
        self._client = boto3.client(
            "s3",
            region_name=region_name,
            config=config,
        )

    def upload_file(self, local_path: Path, s3_uri: S3Uri) -> None:
        """上传文件到 S3。"""
        self._client.upload_file(
            str(local_path),
            s3_uri.bucket,
            s3_uri.key,
        )

    def download_file(self, s3_uri: S3Uri, local_path: Path) -> None:
        """从 S3 下载文件。"""
        self._client.download_file(
            s3_uri.bucket,
            s3_uri.key,
            str(local_path),
        )

    def file_exists(self, s3_uri: S3Uri) -> bool:
        """检查 S3 文件是否存在。"""
        try:
            self._client.head_object(Bucket=s3_uri.bucket, Key=s3_uri.key)
            return True
        except self._client.exceptions.ClientError:
            return False
```

---

## 表现层 (Presentation Layer)

### FastAPI 路由

```python
# src/presentation/api/routes/user_routes.py

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.use_cases.user import CreateUserUseCase, GetUserUseCase
from src.application.exceptions import DuplicateEmailError, UserNotFoundError
from src.presentation.schemas import CreateUserRequest, UserResponse
from src.presentation.api.dependencies import get_create_user_use_case


router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    request: CreateUserRequest,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
) -> UserResponse:
    """创建新用户。

    Args:
        request: 创建用户请求
        use_case: 创建用户用例 (依赖注入)

    Returns:
        创建的用户信息

    Raises:
        HTTPException: 邮箱已存在时返回 409
    """
    try:
        dto = request.to_dto()
        result = use_case.execute(dto)
        return UserResponse.from_dto(result)
    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_EMAIL", "message": str(e)},
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user(
    user_id: UUID,
    use_case: GetUserUseCase = Depends(get_get_user_use_case),
) -> UserResponse:
    """获取用户信息。"""
    try:
        result = use_case.execute(user_id)
        return UserResponse.from_dto(result)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": f"用户 {user_id} 不存在"},
        )
```

### Pydantic Schemas

```python
# src/presentation/schemas/user_schemas.py

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from src.application.dto import CreateUserDTO, UserResponseDTO


class CreateUserRequest(BaseModel):
    """创建用户请求模型。"""

    name: str = Field(..., min_length=1, max_length=100, description="用户名称")
    email: EmailStr = Field(..., description="用户邮箱")

    def to_dto(self) -> CreateUserDTO:
        """转换为 DTO。"""
        return CreateUserDTO(name=self.name, email=self.email)


class UserResponse(BaseModel):
    """用户响应模型。"""

    id: UUID
    name: str
    email: str
    is_active: bool
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: UserResponseDTO) -> "UserResponse":
        """从 DTO 创建响应模型。"""
        return cls(
            id=dto.id,
            name=dto.name,
            email=dto.email,
            is_active=dto.is_active,
            created_at=dto.created_at,
        )

    class Config:
        from_attributes = True
```

---

## 依赖注入

### 依赖容器

```python
# src/presentation/api/dependencies/container.py

from functools import lru_cache

from sqlalchemy.orm import Session

from src.domain.repositories import UserRepository
from src.application.interfaces import EmailService, StorageService
from src.application.use_cases.user import CreateUserUseCase
from src.infrastructure.database import get_db_session
from src.infrastructure.database.repositories import SQLAlchemyUserRepository
from src.infrastructure.external.aws import S3StorageAdapter
from src.infrastructure.external.email import SESEmailService
from src.infrastructure.config import Settings


@lru_cache
def get_settings() -> Settings:
    """获取应用配置 (缓存)。"""
    return Settings()


def get_user_repository(
    session: Session = Depends(get_db_session)
) -> UserRepository:
    """获取用户仓储实例。"""
    return SQLAlchemyUserRepository(session)


def get_email_service() -> EmailService:
    """获取邮件服务实例。"""
    settings = get_settings()
    return SESEmailService(region_name=settings.aws_region)


def get_storage_service() -> StorageService:
    """获取存储服务实例。"""
    settings = get_settings()
    return S3StorageAdapter(region_name=settings.aws_region)


def get_create_user_use_case(
    repository: UserRepository = Depends(get_user_repository),
    email_service: EmailService = Depends(get_email_service),
) -> CreateUserUseCase:
    """获取创建用户用例实例。"""
    return CreateUserUseCase(
        user_repository=repository,
        email_service=email_service,
    )
```

---

## 检查清单

在 PR Review 时，检查以下架构要点：

- [ ] Domain 层没有外部框架依赖
- [ ] Application 层只依赖 Domain 层
- [ ] 仓储接口定义在 Domain 层，实现在 Infrastructure 层
- [ ] 用例只协调，不包含具体实现
- [ ] DTO 在层之间传递数据
- [ ] 依赖注入正确配置
- [ ] 外部服务有对应的接口抽象
- [ ] Presentation 层处理 HTTP 相关逻辑

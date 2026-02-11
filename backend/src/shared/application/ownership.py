"""所有权校验辅助函数，消除各模块 Service 中的重复代码。"""

from typing import TypeVar

from src.shared.domain.base_entity import PydanticEntity
from src.shared.domain.exceptions import ForbiddenError
from src.shared.domain.repositories import IRepository


E = TypeVar("E", bound=PydanticEntity)


async def get_or_raise(
    repo: IRepository[E, int],
    entity_id: int,
    not_found_error_cls: type[Exception],
    *error_args: object,
) -> E:
    """根据 ID 获取实体，不存在则抛出指定异常。

    Raises:
        not_found_error_cls: 实体不存在
    """
    entity = await repo.get_by_id(entity_id)
    if entity is None:
        raise not_found_error_cls(*error_args)
    return entity


def check_ownership(
    entity: PydanticEntity,
    user_id: int,
    *,
    owner_field: str = "owner_id",
    error_code: str = "FORBIDDEN",
) -> None:
    """校验实体所有权，不匹配则抛出 ForbiddenError。

    Raises:
        ForbiddenError: 用户无权操作此资源
    """
    if getattr(entity, owner_field) != user_id:
        raise ForbiddenError(message="无权操作此资源", code=error_code)

"""领域异常体系。"""


class DomainError(Exception):
    """领域层基础异常。"""

    def __init__(self, message: str = "领域错误", code: str = "DOMAIN_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class EntityNotFoundError(DomainError):
    """实体未找到异常 (对应 HTTP 404)。"""

    def __init__(self, *, entity_type: str, entity_id: int | str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(
            message=f"{entity_type}(id={entity_id}) 不存在",
            code=f"NOT_FOUND_{entity_type.upper()}",
        )


class DuplicateEntityError(DomainError):
    """实体重复异常 (对应 HTTP 409)。"""

    def __init__(self, *, entity_type: str, field: str, value: str) -> None:
        self.entity_type = entity_type
        self.field = field
        self.value = value
        super().__init__(
            message=f"{entity_type} 的 {field}={value} 已存在",
            code=f"DUPLICATE_{entity_type.upper()}",
        )


class InvalidStateTransitionError(DomainError):
    """非法状态转换异常 (对应 HTTP 409)。"""

    def __init__(
        self,
        *,
        entity_type: str,
        current_state: str,
        target_state: str,
    ) -> None:
        self.entity_type = entity_type
        self.current_state = current_state
        self.target_state = target_state
        super().__init__(
            message=f"{entity_type} 不能从 {current_state} 转换到 {target_state}",
            code=f"INVALID_STATE_{entity_type.upper()}",
        )


class ValidationError(DomainError):
    """数据验证异常 (对应 HTTP 422)。"""

    def __init__(self, *, message: str, field: str | None = None) -> None:
        self.field = field
        super().__init__(message=message, code="INVALID_INPUT")


class ResourceQuotaExceededError(DomainError):
    """资源配额超限异常 (对应 HTTP 429)。"""

    def __init__(
        self,
        *,
        resource_type: str,
        quota: int,
        requested: int,
    ) -> None:
        self.resource_type = resource_type
        self.quota = quota
        self.requested = requested
        super().__init__(
            message=f"{resource_type} 配额不足: 限额 {quota}, 请求 {requested}",
            code=f"QUOTA_EXCEEDED_{resource_type.upper()}",
        )

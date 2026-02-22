"""builder 模块领域异常。"""

from src.shared.domain.exceptions import DomainError, EntityNotFoundError


class BuilderError(DomainError):
    """Builder 模块基础异常。"""

    def __init__(self, message: str = "Builder 错误", code: str = "BUILDER_ERROR") -> None:
        super().__init__(message=message, code=code)


class BuilderSessionNotFoundError(BuilderError, EntityNotFoundError):
    """Builder 会话不存在。"""

    def __init__(self, session_id: int) -> None:
        EntityNotFoundError.__init__(self, entity_type="BuilderSession", entity_id=session_id)


class BuilderSessionExpiredError(BuilderError):
    """Builder 会话已过期。"""

    def __init__(self, session_id: int) -> None:
        super().__init__(
            message=f"BuilderSession(id={session_id}) 已过期",
            code="BUILDER_SESSION_EXPIRED",
        )


class BuilderInvalidStateError(BuilderError):
    """Builder 会话状态不合法。"""

    def __init__(self, session_id: int, current_status: str, action: str) -> None:
        super().__init__(
            message=f"BuilderSession(id={session_id}) 当前状态 {current_status}, 无法执行 {action}",
            code="BUILDER_INVALID_STATE",
        )

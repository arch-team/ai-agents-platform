"""Skills 模块领域异常。"""

from src.shared.domain.exceptions import EntityNotFoundError


class SkillNotFoundError(EntityNotFoundError):
    """Skill 不存在。"""

    def __init__(self, skill_id: int) -> None:
        super().__init__(entity_type="Skill", entity_id=skill_id)

"""evaluation 模块领域事件。"""

from dataclasses import dataclass

from src.shared.domain.events import DomainEvent


@dataclass
class TestSuiteCreatedEvent(DomainEvent):
    """测试集创建事件。"""

    suite_id: int = 0
    owner_id: int = 0


@dataclass
class TestSuiteActivatedEvent(DomainEvent):
    """测试集激活事件。"""

    suite_id: int = 0


@dataclass
class TestSuiteArchivedEvent(DomainEvent):
    """测试集归档事件。"""

    suite_id: int = 0


@dataclass
class EvaluationRunCompletedEvent(DomainEvent):
    """评估运行完成事件。"""

    run_id: int = 0
    suite_id: int = 0
    user_id: int = 0
    score: float = 0.0

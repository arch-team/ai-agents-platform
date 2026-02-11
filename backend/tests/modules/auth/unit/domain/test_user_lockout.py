"""User 实体账户锁定逻辑单元测试。"""

from datetime import UTC, datetime, timedelta

import pytest

from src.modules.auth.domain.entities.user import User


@pytest.mark.unit
class TestUserLockoutFields:
    """测试 User 实体的锁定相关字段默认值。"""

    def test_default_failed_login_count_is_zero(self) -> None:
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            name="Test",
        )
        assert user.failed_login_count == 0

    def test_default_locked_until_is_none(self) -> None:
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            name="Test",
        )
        assert user.locked_until is None


@pytest.mark.unit
class TestUserRecordFailedLogin:
    """测试登录失败计数递增逻辑。"""

    @pytest.fixture
    def user(self) -> User:
        return User(
            email="test@example.com",
            hashed_password="hashed",
            name="Test",
        )

    def test_increment_failed_count(self, user: User) -> None:
        user.record_failed_login(max_attempts=5, lockout_minutes=30)
        assert user.failed_login_count == 1

    def test_multiple_failures_increment(self, user: User) -> None:
        for _ in range(3):
            user.record_failed_login(max_attempts=5, lockout_minutes=30)
        assert user.failed_login_count == 3

    def test_lock_on_max_attempts(self, user: User) -> None:
        for _ in range(5):
            user.record_failed_login(max_attempts=5, lockout_minutes=30)
        assert user.failed_login_count == 5
        assert user.locked_until is not None

    def test_lock_duration(self, user: User) -> None:
        now = datetime.now(UTC)
        for _ in range(5):
            user.record_failed_login(max_attempts=5, lockout_minutes=30)
        assert user.locked_until is not None
        # 锁定时间应约为 30 分钟后
        expected_min = now + timedelta(minutes=29)
        expected_max = now + timedelta(minutes=31)
        assert expected_min <= user.locked_until <= expected_max

    def test_no_lock_before_max_attempts(self, user: User) -> None:
        for _ in range(4):
            user.record_failed_login(max_attempts=5, lockout_minutes=30)
        assert user.failed_login_count == 4
        assert user.locked_until is None


@pytest.mark.unit
class TestUserIsLocked:
    """测试账户锁定状态检查。"""

    @pytest.fixture
    def user(self) -> User:
        return User(
            email="test@example.com",
            hashed_password="hashed",
            name="Test",
        )

    def test_not_locked_by_default(self, user: User) -> None:
        assert user.is_locked is False

    def test_locked_when_locked_until_in_future(self, user: User) -> None:
        user.locked_until = datetime.now(UTC) + timedelta(minutes=30)
        assert user.is_locked is True

    def test_not_locked_when_locked_until_in_past(self, user: User) -> None:
        user.locked_until = datetime.now(UTC) - timedelta(minutes=1)
        assert user.is_locked is False


@pytest.mark.unit
class TestUserResetFailedLogins:
    """测试登录成功后重置失败计数。"""

    def test_reset_clears_count_and_lock(self) -> None:
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            name="Test",
            failed_login_count=5,
            locked_until=datetime.now(UTC) + timedelta(minutes=30),
        )
        user.reset_failed_logins()
        assert user.failed_login_count == 0
        assert user.locked_until is None

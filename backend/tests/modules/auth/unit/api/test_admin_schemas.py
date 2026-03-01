"""Admin API 请求模型验证测试。

覆盖 src/modules/auth/api/schemas/admin_requests.py 中的验证逻辑。
"""

import pytest
from pydantic import ValidationError

from src.modules.auth.api.schemas.admin_requests import AdminCreateUserRequest, ChangeRoleRequest


@pytest.mark.unit
class TestAdminCreateUserRequest:
    """AdminCreateUserRequest 验证测试。"""

    def test_valid_request(self):
        """有效请求正常创建。"""
        req = AdminCreateUserRequest(
            email="test@example.com",
            password="StrongPwd1",
            name="张三",
        )
        assert req.email == "test@example.com"
        assert req.role == "viewer"

    def test_password_missing_uppercase(self):
        """密码缺少大写字母时验证失败。"""
        with pytest.raises(ValidationError, match="大写字母"):
            AdminCreateUserRequest(
                email="test@example.com",
                password="weakpwd123",
                name="张三",
            )

    def test_password_missing_lowercase(self):
        """密码缺少小写字母时验证失败。"""
        with pytest.raises(ValidationError, match="小写字母"):
            AdminCreateUserRequest(
                email="test@example.com",
                password="STRONGPWD123",
                name="张三",
            )

    def test_password_missing_digit(self):
        """密码缺少数字时验证失败。"""
        with pytest.raises(ValidationError, match="数字"):
            AdminCreateUserRequest(
                email="test@example.com",
                password="StrongPwdNoDigit",
                name="张三",
            )

    def test_invalid_role(self):
        """无效角色值验证失败。"""
        with pytest.raises(ValidationError, match="无效的角色值"):
            AdminCreateUserRequest(
                email="test@example.com",
                password="StrongPwd1",
                name="张三",
                role="superadmin",
            )

    def test_valid_role_admin(self):
        """admin 角色有效。"""
        req = AdminCreateUserRequest(
            email="test@example.com",
            password="StrongPwd1",
            name="张三",
            role="admin",
        )
        assert req.role == "admin"


@pytest.mark.unit
class TestChangeRoleRequest:
    """ChangeRoleRequest 验证测试。"""

    def test_valid_role(self):
        """有效角色正常创建。"""
        req = ChangeRoleRequest(role="admin")
        assert req.role == "admin"

    def test_invalid_role(self):
        """无效角色验证失败。"""
        with pytest.raises(ValidationError, match="无效的角色值"):
            ChangeRoleRequest(role="invalid_role")

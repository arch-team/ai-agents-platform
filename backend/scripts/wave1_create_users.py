#!/usr/bin/env python3
"""
Wave 1 种子用户批量创建脚本
用于 AI Agents Platform 梯度推广第一波用户初始化

使用方法：
  export ADMIN_PASSWORD="your-admin-password"
  export WAVE1_USER_PASSWORD="Wave1@2026!"
  uv run python scripts/wave1_create_users.py
"""

import os
import sys

import httpx


# ==================== 配置 ====================

API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    "http://ai-agents-prod-1419512933.us-east-1.elb.amazonaws.com",
)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
WAVE1_USER_PASSWORD = os.environ.get("WAVE1_USER_PASSWORD", "")

# ==================== Wave 1 用户定义 ====================
# 角色分配：5 名技术人员 + 3 名产品/运营 + 2 名管理者

WAVE1_USERS = [
    # 技术人员（DEVELOPER）
    {"email": "dev01@company.com", "name": "技术用户01", "role": "developer"},
    {"email": "dev02@company.com", "name": "技术用户02", "role": "developer"},
    {"email": "dev03@company.com", "name": "技术用户03", "role": "developer"},
    {"email": "dev04@company.com", "name": "技术用户04", "role": "developer"},
    {"email": "dev05@company.com", "name": "技术用户05", "role": "developer"},
    # 产品/运营（DEVELOPER，从 VIEWER 升级）
    {"email": "pm01@company.com", "name": "产品经理01", "role": "developer"},
    {"email": "ops01@company.com", "name": "运营人员01", "role": "developer"},
    {"email": "hr01@company.com", "name": "HR人员01", "role": "developer"},
    # 管理者（ADMIN）
    {"email": "manager01@company.com", "name": "管理者01", "role": "admin"},
    {"email": "manager02@company.com", "name": "管理者02", "role": "admin"},
]


def validate_env() -> None:
    """验证必要的环境变量"""
    errors = []
    if not ADMIN_PASSWORD:
        errors.append("ADMIN_PASSWORD 未设置（管理员密码必须提供）")
    if not WAVE1_USER_PASSWORD:
        errors.append("WAVE1_USER_PASSWORD 未设置（Wave 1 用户初始密码必须提供）")
    if errors:
        for err in errors:
            print(f"[错误] {err}")
        print("\n请设置环境变量后重试：")
        print('  export ADMIN_PASSWORD="your-admin-password"')
        print('  export WAVE1_USER_PASSWORD="Wave1@2026!"')
        sys.exit(1)


def admin_login(client: httpx.Client) -> str:
    """使用管理员凭证登录，返回 access_token"""
    print(f"[登录] 使用管理员账号 {ADMIN_EMAIL} 登录...")
    response = client.post(
        f"{API_BASE_URL}/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    if response.status_code != 200:
        print(f"[错误] 管理员登录失败，状态码: {response.status_code}")
        print(f"       响应: {response.text}")
        sys.exit(1)

    token = response.json().get("access_token")
    if not token:
        print("[错误] 登录响应中未找到 access_token")
        sys.exit(1)

    print("[登录] 管理员登录成功")
    return token


def create_users(client: httpx.Client, token: str) -> dict:
    """循环创建所有 Wave 1 用户，返回统计结果"""
    headers = {"Authorization": f"Bearer {token}"}
    stats = {"success": 0, "skipped": 0, "failed": 0}

    print(f"\n[创建] 开始创建 {len(WAVE1_USERS)} 个 Wave 1 用户...\n")

    for user in WAVE1_USERS:
        payload = {
            "email": user["email"],
            "password": WAVE1_USER_PASSWORD,
            "name": user["name"],
            "role": user["role"],
        }

        response = client.post(
            f"{API_BASE_URL}/api/v1/admin/users",
            json=payload,
            headers=headers,
        )

        if response.status_code in (200, 201):
            print(f"  [成功] {user['email']} ({user['name']}, {user['role']})")
            stats["success"] += 1
        elif response.status_code == 409:
            print(f"  [跳过] {user['email']} 已存在，跳过创建")
            stats["skipped"] += 1
        else:
            print(f"  [失败] {user['email']} — 状态码: {response.status_code}, 响应: {response.text}")
            stats["failed"] += 1

    return stats


def print_summary(stats: dict) -> None:
    """打印最终汇总"""
    total = stats["success"] + stats["skipped"] + stats["failed"]
    print("\n" + "=" * 50)
    print("Wave 1 用户创建汇总")
    print("=" * 50)
    print(f"  总计：{total} 个用户")
    print(f"  成功：{stats['success']} 个")
    print(f"  跳过：{stats['skipped']} 个（用户已存在）")
    print(f"  失败：{stats['failed']} 个")
    print("=" * 50)

    if stats["failed"] > 0:
        print("\n[警告] 有用户创建失败，请检查以上错误信息")
        sys.exit(1)
    else:
        print("\n[完成] Wave 1 用户初始化完成")


def main() -> None:
    validate_env()

    with httpx.Client(timeout=30.0) as client:
        token = admin_login(client)
        stats = create_users(client, token)

    print_summary(stats)


if __name__ == "__main__":
    main()

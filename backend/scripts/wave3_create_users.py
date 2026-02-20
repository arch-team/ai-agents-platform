#!/usr/bin/env python3
"""
Wave 3 全公司用户批量创建脚本
AI Agents Platform 梯度推广第三波 — 50 人目标

使用方法：
  export ADMIN_PASSWORD="your-admin-password"
  export WAVE3_USER_PASSWORD="Wave3@2026!"
  uv run python scripts/wave3_create_users.py

可选：创建扩展批次（法务/销售/市场/客服/管理层）
  INCLUDE_EXTENDED=1 uv run python scripts/wave3_create_users.py
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
WAVE3_USER_PASSWORD = os.environ.get("WAVE3_USER_PASSWORD", "")
INCLUDE_EXTENDED = os.environ.get("INCLUDE_EXTENDED", "0") == "1"

# ==================== Wave 3 主批次（20 人）====================

WAVE3_USERS_MAIN = [
    # 技术部（5 人，DEVELOPER）
    {"email": "tech06@company.com", "name": "技术用户06", "role": "developer"},
    {"email": "tech07@company.com", "name": "技术用户07", "role": "developer"},
    {"email": "tech08@company.com", "name": "技术用户08", "role": "developer"},
    {"email": "tech09@company.com", "name": "技术用户09", "role": "developer"},
    {"email": "tech10@company.com", "name": "技术用户10", "role": "developer"},
    # 产品部（5 人，1 DEVELOPER + 4 VIEWER）
    {"email": "product03@company.com", "name": "产品用户03", "role": "developer"},
    {"email": "product04@company.com", "name": "产品用户04", "role": "viewer"},
    {"email": "product05@company.com", "name": "产品用户05", "role": "viewer"},
    {"email": "product06@company.com", "name": "产品用户06", "role": "viewer"},
    {"email": "product07@company.com", "name": "产品用户07", "role": "viewer"},
    # 运营部（4 人，VIEWER）
    {"email": "ops03@company.com", "name": "运营用户03", "role": "viewer"},
    {"email": "ops04@company.com", "name": "运营用户04", "role": "viewer"},
    {"email": "ops05@company.com", "name": "运营用户05", "role": "viewer"},
    {"email": "ops06@company.com", "name": "运营用户06", "role": "viewer"},
    # HR（3 人，VIEWER）
    {"email": "hr02@company.com", "name": "HR用户02", "role": "viewer"},
    {"email": "hr03@company.com", "name": "HR用户03", "role": "viewer"},
    {"email": "hr04@company.com", "name": "HR用户04", "role": "viewer"},
    # 财务部（3 人，VIEWER）
    {"email": "finance02@company.com", "name": "财务用户02", "role": "viewer"},
    {"email": "finance03@company.com", "name": "财务用户03", "role": "viewer"},
    {"email": "finance04@company.com", "name": "财务用户04", "role": "viewer"},
]

# ==================== Wave 3 扩展批次（10 人）====================

WAVE3_USERS_EXTENDED = [
    # 法务部（2 人，VIEWER）
    {"email": "legal01@company.com", "name": "法务用户01", "role": "viewer"},
    {"email": "legal02@company.com", "name": "法务用户02", "role": "viewer"},
    # 销售部（3 人，VIEWER）
    {"email": "sales01@company.com", "name": "销售用户01", "role": "viewer"},
    {"email": "sales02@company.com", "name": "销售用户02", "role": "viewer"},
    {"email": "sales03@company.com", "name": "销售用户03", "role": "viewer"},
    # 市场部（2 人，VIEWER）
    {"email": "mkt01@company.com", "name": "市场用户01", "role": "viewer"},
    {"email": "mkt02@company.com", "name": "市场用户02", "role": "viewer"},
    # 客服部（2 人，VIEWER）
    {"email": "cs01@company.com", "name": "客服用户01", "role": "viewer"},
    {"email": "cs02@company.com", "name": "客服用户02", "role": "viewer"},
    # 管理层（1 人，VIEWER）
    {"email": "mgmt03@company.com", "name": "管理用户03", "role": "viewer"},
]


def validate_env() -> None:
    errors = []
    if not ADMIN_PASSWORD:
        errors.append("ADMIN_PASSWORD 未设置")
    if not WAVE3_USER_PASSWORD:
        errors.append("WAVE3_USER_PASSWORD 未设置")
    if errors:
        for err in errors:
            print(f"[错误] {err}")
        print("\n请设置环境变量后重试：")
        print('  export ADMIN_PASSWORD="your-admin-password"')
        print('  export WAVE3_USER_PASSWORD="Wave3@2026!"')
        sys.exit(1)


def admin_login(client: httpx.Client) -> str:
    print(f"[登录] 管理员 {ADMIN_EMAIL} 登录...")
    response = client.post(
        f"{API_BASE_URL}/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    if response.status_code != 200:
        print(f"[错误] 登录失败 {response.status_code}: {response.text}")
        sys.exit(1)
    token = response.json().get("access_token")
    if not token:
        print("[错误] 响应中未找到 access_token")
        sys.exit(1)
    print("[登录] 成功")
    return token


def create_users(client: httpx.Client, token: str, users: list[dict]) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    stats: dict[str, int] = {"success": 0, "skipped": 0, "failed": 0}

    for user in users:
        payload = {
            "email": user["email"],
            "password": WAVE3_USER_PASSWORD,
            "name": user["name"],
            "role": user["role"],
        }
        response = client.post(
            f"{API_BASE_URL}/api/v1/admin/users",
            json=payload,
            headers=headers,
        )
        if response.status_code in (200, 201):
            print(f"  ✅ {user['email']} ({user['name']}, {user['role']})")
            stats["success"] += 1
        elif response.status_code == 409:
            print(f"  ⏭️  {user['email']} 已存在，跳过")
            stats["skipped"] += 1
        else:
            print(f"  ❌ {user['email']} — {response.status_code}: {response.text}")
            stats["failed"] += 1

    return stats


def main() -> None:
    validate_env()

    users_to_create = WAVE3_USERS_MAIN.copy()
    if INCLUDE_EXTENDED:
        users_to_create += WAVE3_USERS_EXTENDED
        print(f"\n[模式] 主批次 + 扩展批次（共 {len(users_to_create)} 人）")
    else:
        print(f"\n[模式] 主批次（{len(users_to_create)} 人）")

    print(f"[目标] {API_BASE_URL}\n")

    with httpx.Client(timeout=30.0) as client:
        token = admin_login(client)
        print(f"\n[创建] 开始创建 {len(users_to_create)} 个 Wave 3 用户...\n")
        stats = create_users(client, token, users_to_create)

    total = sum(stats.values())
    print("\n" + "=" * 50)
    print("Wave 3 用户创建汇总")
    print("=" * 50)
    print(f"  总计：{total} | 成功：{stats['success']} | 跳过：{stats['skipped']} | 失败：{stats['failed']}")
    print("=" * 50)

    if stats["failed"] > 0:
        print("\n[警告] 有用户创建失败，请检查以上错误信息")
        sys.exit(1)
    else:
        print("\n[完成] Wave 3 用户初始化完成 🎉")
        print("       初始密码：Wave3@2026!（用户首次登录后需修改）")


if __name__ == "__main__":
    main()

# 安全规范 (Security Standards)

> **职责**: 安全规范，定义禁止事项、必须事项和安全检测命令。

---

## 0. 速查卡片

> Claude 生成代码时优先查阅此章节

### 安全规则速查表

| 规则 | ❌ 禁止 | ✅ 正确 |
|------|--------|--------|
| 硬编码密钥 | `API_KEY = "sk-xxx"` | `settings.api_key` (环境变量) |
| SQL 注入 | `f"SELECT * WHERE id='{x}'"` | `session.query().filter()` |
| 命令注入 | `os.system(user_input)` | 参数化命令或白名单 |
| 路径遍历 | `open(f"/uploads/{name}")` | `Path(name).name` 验证 |
| 敏感日志 | `logger.info(f"密码: {pwd}")` | 仅记录非敏感信息 |
| 危险函数 | `eval(user_input)` | `json.loads()` / Pydantic |

### 安全检测命令

```bash
# 完整安全检查
uv run bandit -r src/ && uv run safety check && uv run pip-audit

# 按类别检测
grep -rE "(password|secret|key|token)\s*=\s*['\"][^'\"]+['\"]" src/  # 硬编码密钥
grep -rE "f['\"].*SELECT|os\.system|subprocess\.call.*shell=True" src/  # 注入攻击
grep -rE "\beval\s*\(|\bexec\s*\(|pickle\.loads" src/                  # 危险函数
grep -rE "logger\.(info|debug|error).*password" src/                    # 敏感日志
```

---

## 1. 易错写法补充

> 速查表已列出核心 ❌/✅ 对比，以下补充易错的正确写法。

```python
# SQL 参数绑定 - 使用 SQLAlchemy text() 而非 f-string
stmt = text("SELECT * FROM users WHERE id = :user_id")
session.execute(stmt, {"user_id": user_id})

# 路径遍历防护 - 使用 Path.name 移除 ../ 组件
safe_name = Path(filename).name
file_path = Path("/uploads") / safe_name
```

---

## 2. 强制要求

| 要求 | 规范 | 关键约束 |
|------|------|---------|
| **环境变量** | `pydantic_settings.BaseSettings` | 敏感字段使用 `SecretStr` 类型 |
| **输入验证** | Pydantic `Field` + `field_validator` | 密码: 8~128 字符，含大小写+数字 |
| **密码存储** | `passlib` bcrypt | `bcrypt__rounds=12` |
| **登录限制** | 登录失败锁定 | 5 次失败 → 锁定 30 分钟 |
| **错误响应** | 通用错误信息 | ❌ 禁止返回 `str(e)` 或 traceback，详见 [architecture.md](architecture.md) §8 |
| **访问控制** | OAuth2 + RBAC | `get_current_user` → `require_role` 依赖链 |

---

## 相关文档

- [checklist.md](checklist.md) §安全 - PR Review 检查清单
- [logging.md](logging.md) - 日志脱敏规则

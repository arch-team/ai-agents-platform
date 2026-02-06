# API 设计规范 (API Design Standards)

> **职责**: API 设计规范，定义 RESTful 路由、HTTP 状态码和错误响应格式。

> Claude 生成 API 代码时优先查阅此文档

---

## RESTful 路由命名

```python
# ✅ 正确 - 使用复数名词
GET    /api/v1/users          # 获取用户列表
GET    /api/v1/users/{id}     # 获取单个用户
POST   /api/v1/users          # 创建用户
PUT    /api/v1/users/{id}     # 更新用户
DELETE /api/v1/users/{id}     # 删除用户

# ❌ 错误 - 使用动词
POST   /api/v1/createUser
GET    /api/v1/getUserById
```

---

## HTTP 状态码

| 状态码 | 场景 |
|--------|------|
| 200 | 成功 (GET, PUT) |
| 201 | 创建成功 (POST) |
| 204 | 删除成功 (DELETE) |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 验证错误 |
| 500 | 服务器内部错误 |

---

## 错误响应格式

```python
class ErrorResponse(BaseModel):
    code: str           # 前缀: INVALID_, NOT_FOUND_, DUPLICATE_, FORBIDDEN_, INTERNAL_
    message: str        # 人类可读的错误信息
    details: dict | None = None
```

---

## 分页规范

| 参数/字段 | 类型 | 说明 |
|-----------|------|------|
| `page` | int | 页码，从 1 开始，默认 1 |
| `page_size` | int | 每页数量，默认 20，最大 100 |
| `total` | int | 总记录数 (响应) |
| `total_pages` | int | 总页数 (响应) |
| `items` | list[T] | 数据列表 (响应) |

---

## 命名约定

| 元素 | 规范 | 示例 |
|------|------|------|
| 路由路径 | `kebab-case` | `/training-jobs` |
| 查询参数 | `snake_case` | `?page_size=20` |
| 请求/响应字段 | `snake_case` | `{"created_at": "..."}` |

---

## 版本控制

- URL 路径版本: `/api/v1/`, `/api/v2/`
- 至少维护 2 个主版本

---

## PR Review 检查清单

完整检查清单见 [checklist.md](checklist.md) §API 设计

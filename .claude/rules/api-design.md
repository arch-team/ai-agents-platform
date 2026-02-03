# API 设计规范 (API Design Standards)

本文档定义 Python 后端项目的 RESTful API 设计规范。

---

## 0. 速查卡片 (Quick Reference)

> Claude 生成代码时优先查阅此章节

### RESTful 路由命名

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

### HTTP 状态码速查

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

### PR Review 检查清单

- [ ] 路由使用复数名词，不使用动词
- [ ] HTTP 方法语义正确 (GET 读取, POST 创建, PUT 更新, DELETE 删除)
- [ ] 返回正确的 HTTP 状态码
- [ ] 错误响应使用标准格式
- [ ] 分页参数使用 `page` 和 `page_size`

---

## 1. 错误响应格式

```python
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    """标准错误响应格式。"""
    code: str           # 错误代码，如 "USER_NOT_FOUND"
    message: str        # 人类可读的错误信息
    details: dict | None = None  # 可选的详细信息
```

### 错误代码命名规范

| 前缀 | 场景 | 示例 |
|------|------|------|
| `INVALID_` | 参数验证失败 | `INVALID_EMAIL_FORMAT` |
| `NOT_FOUND_` | 资源不存在 | `NOT_FOUND_USER` |
| `DUPLICATE_` | 资源冲突 | `DUPLICATE_EMAIL` |
| `FORBIDDEN_` | 权限不足 | `FORBIDDEN_RESOURCE` |
| `INTERNAL_` | 服务器错误 | `INTERNAL_ERROR` |

---

## 2. 分页规范

### 请求参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码 (从 1 开始) |
| `page_size` | int | 20 | 每页数量 (最大 100) |

### 响应格式

```python
class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式。"""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
```

---

## 3. 版本控制

- URL 路径版本: `/api/v1/`, `/api/v2/`
- 主版本号递增: 不兼容的 API 变更
- 旧版本保留: 至少维护 2 个主版本

---

## 4. 命名约定

| 元素 | 规范 | 示例 |
|------|------|------|
| 路由路径 | `kebab-case` | `/training-jobs` |
| 查询参数 | `snake_case` | `?page_size=20` |
| 请求体字段 | `snake_case` | `{"user_name": "张三"}` |
| 响应体字段 | `snake_case` | `{"created_at": "..."}` |

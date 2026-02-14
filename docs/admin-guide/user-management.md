# 用户管理

> 本指南说明 ADMIN 角色如何管理用户账户、分配角色、审计用户行为。

---

## 目录

- [用户模型](#用户模型)
- [角色分配](#角色分配)
- [账户管理](#账户管理)
- [用户注册控制](#用户注册控制)
- [安全策略](#安全策略)
- [审计日志查看](#审计日志查看)
- [API 参考](#api-参考)
- [常见问题](#常见问题)

---

## 用户模型

每个用户账户包含以下属性:

| 属性 | 说明 |
|------|------|
| id | 用户唯一标识 |
| email | 登录邮箱 (全局唯一) |
| name | 用户姓名 |
| role | 角色: ADMIN / DEVELOPER / VIEWER |
| is_active | 账户启用状态 |
| created_at | 创建时间 |

---

## 角色分配

### 三种角色

| 角色 | 定位 | 典型人群 |
|------|------|---------|
| **ADMIN** | 平台管理员 | IT 管理员、技术负责人 |
| **DEVELOPER** | 开发者/内容创作者 | 工程师、产品经理、运营人员 |
| **VIEWER** | 查看者/使用者 | 普通员工、业务人员 |

### 角色分配原则

- **最小权限原则**: 分配满足工作需要的最低角色
- **ADMIN 账户限制**: 建议 ADMIN 账户数量不超过 3 个
- **定期审查**: 建议每季度审查一次用户角色分配

### 变更角色

通过 API 或数据库操作变更用户角色。变更后:

- 用户下次使用 Refresh Token 续期时获取新角色权限
- 建议通知用户重新登录以立即生效

---

## 账户管理

### 创建用户

**方式一**: 用户自助注册（需开启注册功能）

```
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@company.com",
  "password": "SecurePassword123",
  "name": "张三"
}
```

注册用户默认角色为 VIEWER。

**方式二**: ADMIN 通过 API 创建

ADMIN 可直接调用注册接口为新用户创建账号。

### 停用账户

停用用户账户后:

- 用户无法登录
- 用户持有的有效 Token 在请求时返回 401
- 用户创建的 Agent、工具、知识库等资源保留
- 账户可随时重新启用

### 启用账户

重新启用已停用的账户，用户即可正常登录和使用。

---

## 用户注册控制

平台通过环境变量 `REGISTRATION_ENABLED` 控制自助注册功能:

| 配置值 | 行为 |
|--------|------|
| `true` | 允许自助注册 (默认) |
| `false` | 关闭自助注册，仅 ADMIN 可创建账户 |

### 注册限流

为防止恶意注册，注册接口配置了速率限制: **3 次/小时** (基于 IP)。

### 推荐策略

| 场景 | 推荐配置 |
|------|---------|
| 内部试用期 | 开启注册，新用户默认 VIEWER |
| 正式运营 | 关闭注册，ADMIN 统一创建账户 |
| 推广期 | 开启注册，ADMIN 定期审核升级角色 |

---

## 安全策略

### 密码策略

- 最小长度: 8 字符
- 最大长度: 128 字符
- 存储: bcrypt 哈希 (rounds=12)

### 登录安全

| 策略 | 配置 |
|------|------|
| 登录失败锁定 | 5 次失败 -> 锁定 30 分钟 |
| 登录速率限制 | 5 次/分钟 (基于 IP) |
| Token 有效期 | Access Token 30 分钟 |
| Refresh Token | 支持续期和撤销 |

### Token 管理

- **Access Token**: JWT 格式，包含 user_id、email、role 信息，有效期 30 分钟
- **Refresh Token**: 用于换取新的 Access Token，登出时撤销
- **Token 刷新**: `POST /api/v1/auth/refresh`，速率限制 10 次/分钟

### 账户锁定

用户登录失败达到阈值后账户自动锁定:

- 锁定时间: 30 分钟
- 返回状态码: 423 (Locked)
- 锁定期间即使密码正确也无法登录
- 锁定自动解除，ADMIN 也可手动解锁

---

## 审计日志查看

### 审计范围

平台记录以下类型的操作审计:

| 类别 | 审计事件 |
|------|---------|
| **Agent** | 创建、更新、激活、归档、删除 |
| **对话** | 创建对话 |
| **团队执行** | 启动、完成、失败 |
| **工具** | 创建、更新、删除、提交、审批、拒绝、废弃 |
| **知识库** | 创建、激活、删除、文档上传 |
| **模板** | 创建、发布、归档 |
| **HTTP 请求** | 所有 API 调用 (方法、路径、状态码、耗时) |

### 查看审计日志

```
GET /api/v1/audit-logs?page=1&page_size=20
Authorization: Bearer <admin_token>
```

### 筛选查询

| 参数 | 说明 | 示例 |
|------|------|------|
| category | 按类别筛选 | `?category=agent` |
| action | 按操作筛选 | `?action=agent_created` |
| actor_id | 按操作人筛选 | `?actor_id=1` |
| resource_type | 按资源类型筛选 | `?resource_type=agent` |
| resource_id | 按资源 ID 筛选 | `?resource_id=42` |
| start_date | 开始日期 | `?start_date=2026-02-01` |
| end_date | 结束日期 | `?end_date=2026-02-14` |

### 按资源查询

查看特定资源的完整操作历史:

```
GET /api/v1/audit-logs/resource/agent/42
```

### 审计统计

```
GET /api/v1/audit-logs/stats
```

返回按类别和操作类型的统计汇总。

### 导出 CSV

```
GET /api/v1/audit-logs/export?start_date=2026-02-01&end_date=2026-02-14
```

导出为 UTF-8 CSV 文件，最大 100,000 行，包含完整审计字段。

---

## API 参考

### 认证端点

| 方法 | 路径 | 说明 | 速率限制 |
|------|------|------|---------|
| POST | `/api/v1/auth/register` | 注册用户 | 3 次/小时 |
| POST | `/api/v1/auth/login` | 登录 | 5 次/分钟 |
| POST | `/api/v1/auth/refresh` | 刷新 Token | 10 次/分钟 |
| POST | `/api/v1/auth/logout` | 登出 | - |
| GET | `/api/v1/auth/me` | 当前用户信息 | - |

### 审计日志端点 (ADMIN)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/audit-logs` | 审计日志列表 (分页+筛选) |
| GET | `/api/v1/audit-logs/stats` | 审计统计 |
| GET | `/api/v1/audit-logs/resource/{type}/{id}` | 按资源查询 |
| GET | `/api/v1/audit-logs/export` | 导出 CSV |
| GET | `/api/v1/audit-logs/{id}` | 审计日志详情 |

---

## 常见问题

### Q1: 忘记 ADMIN 密码怎么办？

当前版本不提供密码重置功能。需要通过数据库直接更新密码哈希值，或联系运维人员处理。

### Q2: 如何批量创建用户？

当前版本不提供批量用户创建接口。可通过脚本循环调用注册 API 实现:

```bash
# 示例: 通过脚本批量创建
for user in users.csv; do
  curl -X POST /api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$email\",\"password\":\"$password\",\"name\":\"$name\"}"
done
```

### Q3: 审计日志保留多长时间？

审计日志采用 append-only 模式存储在 Aurora MySQL 中，不会自动清理。建议定期导出归档，并根据企业合规要求制定数据保留策略。

### Q4: 用户被锁定后如何解锁？

用户登录失败 5 次后自动锁定 30 分钟。两种解锁方式:

1. **等待自动解锁**: 30 分钟后锁定自动解除
2. **ADMIN 手动解锁**: 通过数据库或 API 重置锁定状态

### Q5: 如何追踪某个用户的所有操作？

使用审计日志的 actor_id 筛选:

```
GET /api/v1/audit-logs?actor_id=5&start_date=2026-02-01
```

也可以导出该用户的所有操作记录:

```
GET /api/v1/audit-logs/export?actor_id=5
```

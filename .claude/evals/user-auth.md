## EVAL: user-auth
Created: 2026-02-17

### Capability Evals

#### 注册
- [ ] POST /api/v1/auth/register 创建新用户，返回 201
- [ ] 邮箱唯一性校验，重复返回 409
- [ ] 密码使用 bcrypt 哈希存储 (不明文)
- [ ] 注册开关关闭时 (REGISTRATION_ENABLED=False) 返回 403
- [ ] 注册接口 Rate Limiting: 3 次/小时

#### 登录
- [ ] POST /api/v1/auth/login 返回 JWT Access Token + Refresh Token
- [ ] 错误密码返回 401
- [ ] 不存在用户返回 401
- [ ] 停用用户 (is_active=False) 返回 401
- [ ] 登录接口 Rate Limiting: 5 次/分钟

#### 账户锁定
- [ ] 连续 5 次登录失败后账户锁定
- [ ] 锁定持续 30 分钟
- [ ] 锁定期间登录返回 423
- [ ] 锁定到期后可正常登录
- [ ] 成功登录重置失败计数

#### Token 管理
- [ ] POST /api/v1/auth/refresh 刷新 Access Token，返回 200
- [ ] Refresh Token Rotation: 刷新时撤销旧 Token + 签发新 Token
- [ ] 使用已撤销的 Refresh Token 返回 401
- [ ] POST /api/v1/auth/logout 撤销 Refresh Token
- [ ] 刷新接口 Rate Limiting: 10 次/分钟

#### 当前用户
- [ ] GET /api/v1/auth/me 返回当前用户信息
- [ ] 无效/过期 JWT 返回 401
- [ ] 停用用户持有有效 JWT 时请求返回 401

#### RBAC 权限
- [ ] ADMIN 角色可访问管理端点
- [ ] DEVELOPER 角色可创建 Agent 等操作
- [ ] VIEWER 角色只读访问
- [ ] 权限不足返回 403
- [ ] require_role() 依赖工厂正确校验多角色

#### 安全审计
- [ ] 登录成功/失败事件记录 structlog
- [ ] 账户锁定事件记录 structlog
- [ ] Token 刷新事件记录 structlog

### Regression Evals

#### JWT 机制
- [ ] JWT payload 包含 sub, exp, iat, jti, role
- [ ] JWT 使用 PyJWT 库编解码 (非自行实现)
- [ ] Token 过期时间配置正确 (Access: 短, Refresh: 长)

#### 密码服务
- [ ] bcrypt 哈希与验证功能正常
- [ ] 密码哈希不可逆

#### 数据库
- [ ] User ORM 模型字段与实体一致
- [ ] RefreshToken ORM 模型正常
- [ ] Alembic 迁移可正确执行

#### 跨模块影响
- [ ] get_current_user 依赖注入在所有模块中正常工作
- [ ] require_role 装饰器不影响非限制端点

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals

### Test Commands
```bash
# 域实体测试
pytest backend/tests/modules/auth/unit/domain/ -v

# 应用服务测试
pytest backend/tests/modules/auth/unit/application/ -v

# API 测试
pytest backend/tests/modules/auth/unit/api/ -v

# 集成测试
pytest backend/tests/modules/auth/integration/ -v

# 全量
pytest backend/tests/modules/auth/ -v --tb=short
```

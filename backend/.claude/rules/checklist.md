# PR Review 检查清单

> **职责**: PR Review 检查清单的**单一真实源**，涵盖架构、代码风格、安全、测试和 API 设计检查项。

---

## 分层与架构

- [ ] Domain 层没有外部框架依赖 (FastAPI, SQLAlchemy, boto3)
- [ ] Domain 层实体使用 Pydantic BaseModel 或 PydanticEntity 基类
- [ ] Application 层只依赖 Domain 层和接口
- [ ] 仓储接口定义在 Domain 层，实现在 Infrastructure 层
- [ ] API 层通过 Application Services 执行业务操作
- [ ] 模块 Domain 层没有导入其他模块
- [ ] 模块间通信使用 EventBus 或 shared/interfaces
- [ ] `__init__.py` 只导出公开 API，不导出实现细节

详见 [architecture.md](architecture.md)

---

## 代码风格

- [ ] 所有公共接口都有类型提示
- [ ] 没有使用 `Any` 类型
- [ ] 命名符合规范 (snake_case/PascalCase)
- [ ] Docstring 遵循"类型即文档"原则 (类型自解释时省略)
- [ ] 没有通配符导入
- [ ] 异步代码正确使用 async/await

详见 [code-style.md](code-style.md)

---

## 安全

- [ ] 没有硬编码的密钥或密码
- [ ] 所有用户输入都经过验证
- [ ] 使用参数化查询，没有 SQL 拼接
- [ ] 敏感信息不会写入日志
- [ ] 没有使用 eval/exec/pickle
- [ ] 密码使用安全哈希算法存储
- [ ] 错误响应不暴露内部信息

详见 [security.md](security.md)

---

## 测试

- [ ] 测试在 `tests/modules/{module}/`
- [ ] AAA 模式 + 清晰命名
- [ ] Mock 仅边界依赖 + 可独立运行
- [ ] 使用测试标记 (`@pytest.mark.unit` 等)
- [ ] 覆盖率达标 (≥85%)

详见 [testing.md](testing.md)

---

## API 设计

- [ ] 路由使用复数名词，不使用动词
- [ ] HTTP 方法语义正确
- [ ] 返回正确的 HTTP 状态码
- [ ] 错误响应使用 ErrorResponse 格式
- [ ] 分页参数使用 `page` 和 `page_size`

详见 [api-design.md](api-design.md)

---

## SDK 使用

- [ ] 优先使用官方 SDK
- [ ] 自定义实现有充分理由
- [ ] 封装层 < 100 行
- [ ] SDK 异常转换为域异常

详见 [sdk-first.md](sdk-first.md)

---

## 日志

- [ ] 使用 structlog 结构化键值对，不使用字符串拼接
- [ ] 敏感数据已脱敏（密码、Token、邮箱）
- [ ] 没有使用 `print()` 调试输出
- [ ] 异常记录使用 `log.exception()` 而非 `log.warning()`（保留完整 traceback）
- [ ] lifespan/startup 函数的异常处理和普通函数对称（all use `log.exception`）

详见 [logging.md](logging.md)

---

## 可观测性

- [ ] Health Check 端点 (`/health`, `/health/ready`) 可用
- [ ] 关键操作有 Span 或 Metrics 记录
- [ ] Correlation ID 在请求链路中传递

详见 [observability.md](observability.md)

---

## 项目结构

- [ ] 新文件放置在正确目录
- [ ] 测试在 `tests/` 下，镜像 `src/` 结构
- [ ] 新 Python 包有 `__init__.py`
- [ ] 无临时文件被提交

详见 [project-structure.md](project-structure.md)

---

## Task 完成验收（编码任务必检）

> **触发时机**: 每个编码 Task 标记"已完成"之前，必须逐条确认。
> **背景**: 防止"核心功能完成即标记完成"的偏差，确保交付物完整。

### 计划对照

- [ ] 实施方案中该 Task 的所有 `- [ ]` 子项均已实现
- [ ] Task 描述中提到的"Test"类型交付物（单元测试 + 集成测试）均已创建
- [ ] 如涉及新模块注册：main.py (router + 异常映射) + migrations/env.py (ORM import) 已更新

### 参考模块一致性

- [ ] 新模块与参考模块（如 agents）做结构 diff，确认无遗漏文件类型：
  - `domain/events.py` — 领域事件
  - `__init__.py` — 各层级导出（module / api / application / domain）
  - `infrastructure/services/` — 跨模块 Querier 实现（如需要）
  - `integration/` — Repository 集成测试 + API 端点集成测试
- [ ] 新增的 `shared/domain/interfaces/` 接口已在 `providers.py` 注册工厂函数

### 验收命令

```bash
# 结构 diff（将 agents 替换为新模块名）
diff <(find src/modules/agents -name "*.py" -not -path "*__pycache__*" | sed 's|agents|{新模块}|g' | sort) \
     <(find src/modules/{新模块} -name "*.py" -not -path "*__pycache__*" | sort)
```

---

## 预提交一键验证

```bash
uv run ruff check src/ && uv run ruff format --check src/ && uv run mypy src/ && uv run pytest --cov=src --cov-fail-under=85
```

# SDK 优先 (SDK-First)

> **职责**: SDK 优先原则，定义 SDK 决策流程和异常处理模式。

> Claude 生成代码时优先查阅

**核心原则**: 尽可能使用 SDK 简化代码实现，避免重复造轮子。

---

## SDK 决策流程

```
需要实现某功能?
    ↓
官方 SDK 支持? ──是──► 🟢 直接使用 SDK
    │
   否
    ↓
社区库评估通过? ──是──► 🟡 使用社区库
    │
   否
    ↓
🔴 自定义实现 (需 Tech Lead 审批)
```

---

## 优先级说明

### 🟢 优先级 1: 直接使用官方 SDK

无需封装，直接调用。

### 🟡 优先级 2: SDK + 薄封装层

**封装原则**: < 100 行 | 不改变 SDK 行为 | 暴露原生类型

### 🟡 优先级 3: 社区库

| 指标 | 最低要求 |
|------|---------|
| GitHub Stars | > 1,000 |
| 最近提交 | < 3 个月 |
| 许可证 | MIT / Apache 2.0 |

### 🔴 优先级 4: 自定义实现

**必须流程**: research.md 记录 → 说明理由 → Tech Lead 审批

---

## 项目 SDK 版本

所有 SDK 版本要求见 [tech-stack.md](tech-stack.md)（单一真实源）。

---

## SDK 异常处理

```python
# 模式: SDK 异常 → 域异常
try:
    self._client.operation(...)
except ClientError as e:
    raise DomainError(f"操作失败: {e}") from e
```

| SDK | 原始异常 | 域异常 | HTTP |
|-----|---------|--------|------|
| boto3 | `ClientError (NoSuchKey)` | `EntityNotFoundError` | 404 |
| boto3 | `ClientError (AccessDenied)` | `PermissionError` | 403 |
| SQLAlchemy | `IntegrityError` | `DuplicateEntityError` | 409 |

---

## 反模式

```python
# ❌ 过度封装 - 模糊接口，隐藏 SDK 行为
class SuperAwesomeS3Wrapper:
    def magic_upload(self, thing): ...

# ✅ 薄封装 - 明确接口，直接委托 SDK
class S3Adapter:
    def upload_file(self, local: Path, uri: S3Uri) -> None:
        self._client.upload_file(str(local), uri.bucket, uri.key)
```

---

## 检测命令

```bash
# 检测过度封装 (>100 行的适配器)
find src/ -name "*adapter*.py" -exec wc -l {} \; | awk '$1 > 100 {print}'
```

---

## PR Review 检查清单

完整检查清单见 [checklist.md](checklist.md) §SDK 使用

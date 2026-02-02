# SDK 优先 (SDK-First)
**核心原则**：尽可能使用 SDK 简化代码实现，避免重复造轮子。

## 决策级别说明

### 🟢 优先级 1: 直接使用官方 SDK

**适用场景**:
- AWS 服务集成 (SageMaker, S3, DynamoDB)
- 标准 API 调用 (训练任务提交、数据上传下载)
- 官方文档有明确示例

**示例**:

```python
# ✅ 正确: 直接使用 boto3 S3 客户端
import boto3
from botocore.config import Config

config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
s3_client = boto3.client("s3", config=config)

# 上传文件
s3_client.upload_file("local_file.txt", "my-bucket", "remote/path/file.txt")

# 下载文件
s3_client.download_file("my-bucket", "remote/path/file.txt", "local_file.txt")
```

### 🟡 优先级 2: SDK + 薄封装层

**适用场景**:
- SDK 功能不完全满足需求
- 需要统一错误处理或重试逻辑
- 需要适配 Clean Architecture 的端口/适配器模式

**封装原则**:
- 封装层 < 100 行代码
- 不改变 SDK 核心行为
- 暴露 SDK 原生类型，避免过度抽象

**示例**:

```python
# ✅ 正确: 薄封装适配 Clean Architecture
from pathlib import Path
from abc import ABC, abstractmethod
import boto3

# 应用层接口 (端口)
class StorageService(ABC):
    @abstractmethod
    def upload_file(self, local_path: Path, remote_key: str) -> None:
        ...

# 基础设施层实现 (适配器)
class S3StorageAdapter(StorageService):
    """S3 存储适配器 - 封装 < 50 行。"""

    def __init__(self, bucket: str, region: str = "us-west-2") -> None:
        self._bucket = bucket
        self._client = boto3.client("s3", region_name=region)

    def upload_file(self, local_path: Path, remote_key: str) -> None:
        self._client.upload_file(str(local_path), self._bucket, remote_key)
```

### 🟡 优先级 3: 评估后使用社区库

**评估标准**:
| 指标 | 最低要求 |
|------|---------|
| GitHub Stars | > 1,000 |
| 最近提交 | < 3 个月 |
| 开放 Issues | < 100 (或有活跃维护) |
| 文档质量 | 有完整 API 文档 |
| 许可证 | MIT / Apache 2.0 |

### 🔴 优先级 4: 自定义实现 (需审批)

**触发条件**:
- 官方 SDK 和社区库都不满足需求
- 性能要求超出现有方案
- 安全合规有特殊限制

**必须流程**:
1. 在 `research.md` 中记录调研过程
2. 说明为何现有方案不可行
3. 估算自定义实现的维护成本
4. 获得 Tech Lead 审批

---

## 本项目核心 SDK 清单

| 领域 | 官方 SDK | 用途 |
|------|---------|------|
| **训练调度** | `sagemaker` | HyperPod 训练任务管理 |
| **AWS 基础** | `boto3` | S3, DynamoDB, IAM 等服务 |
| **分布式训练** | `torch.distributed` | DDP, FSDP 分布式策略 |
| **深度优化** | `deepspeed` | ZeRO 优化、混合精度 |
| **CDK 部署** | `aws-cdk-lib` | 基础设施即代码 |
| **API 框架** | `fastapi` | REST API 服务 |
| **数据验证** | `pydantic` | 请求/响应模型 |

## 反模式 (Anti-Patterns)

```python
# ❌ 错误: 重新实现 SDK 已有功能
def upload_to_s3(file_path: str, bucket: str, key: str):
    with open(file_path, 'rb') as f:
        # 手动实现分片上传...
        pass

# ✅ 正确: 使用 boto3 的 multipart upload
s3_client.upload_file(file_path, bucket, key, Config=transfer_config)
```

```python
# ❌ 错误: 过度封装，隐藏 SDK 行为
class SuperAwesomeS3Wrapper:
    def magic_upload(self, thing):  # 模糊的接口
        # 500 行封装代码...
        pass

# ✅ 正确: 薄封装，保持 SDK 语义
class S3StorageAdapter:
    def upload_file(self, local_path: Path, s3_uri: S3Uri) -> None:
        self._client.upload_file(str(local_path), s3_uri.bucket, s3_uri.key)
```

## 检查清单

在 PR Review 时，检查以下项目:
- [ ] 是否优先使用了官方 SDK？
- [ ] 自定义实现是否有充分理由？
- [ ] 封装层是否保持薄且透明？
- [ ] 是否避免了重复造轮子？

"""AgentCore Gateway 认证服务接口。"""

from abc import ABC, abstractmethod


class IGatewayAuthService(ABC):
    """AgentCore Gateway 认证服务接口。"""

    @abstractmethod
    async def get_bearer_token(self) -> str:
        """获取 Gateway Bearer Token。

        返回有效的 Bearer Token 字符串。
        获取失败时返回空字符串（触发降级逻辑）。
        """
        ...

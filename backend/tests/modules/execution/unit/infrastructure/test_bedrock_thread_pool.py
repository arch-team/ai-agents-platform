"""Bedrock LLM Client 专用线程池测试。"""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import pytest

from src.modules.execution.infrastructure.external.bedrock_llm_client import BedrockLLMClient


@pytest.mark.unit
class TestBedrockThreadPool:
    """BedrockLLMClient 使用专用线程池。"""

    def test_client_has_executor(self) -> None:
        """客户端包含 ThreadPoolExecutor。"""
        mock_client = MagicMock()
        llm_client = BedrockLLMClient(mock_client)
        assert isinstance(llm_client._executor, ThreadPoolExecutor)

    def test_default_max_workers(self) -> None:
        """默认 max_workers=50。"""
        mock_client = MagicMock()
        llm_client = BedrockLLMClient(mock_client)
        assert llm_client._executor._max_workers == 50

    def test_custom_max_workers(self) -> None:
        """可自定义 max_workers。"""
        mock_client = MagicMock()
        llm_client = BedrockLLMClient(mock_client, max_workers=10)
        assert llm_client._executor._max_workers == 10

    def test_thread_name_prefix(self) -> None:
        """线程名前缀为 bedrock。"""
        mock_client = MagicMock()
        llm_client = BedrockLLMClient(mock_client)
        assert llm_client._executor._thread_name_prefix == "bedrock"

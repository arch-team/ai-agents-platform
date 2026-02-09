"""ToolConfig 值对象单元测试。"""

import pytest

from src.modules.tool_catalog.domain.value_objects.tool_config import ToolConfig


@pytest.mark.unit
class TestToolConfigDefaults:
    def test_default_server_url(self) -> None:
        config = ToolConfig()
        assert config.server_url == ""

    def test_default_transport(self) -> None:
        config = ToolConfig()
        assert config.transport == "stdio"

    def test_default_endpoint_url(self) -> None:
        config = ToolConfig()
        assert config.endpoint_url == ""

    def test_default_method(self) -> None:
        config = ToolConfig()
        assert config.method == "POST"

    def test_default_headers(self) -> None:
        config = ToolConfig()
        assert config.headers == ()

    def test_default_runtime(self) -> None:
        config = ToolConfig()
        assert config.runtime == ""

    def test_default_handler(self) -> None:
        config = ToolConfig()
        assert config.handler == ""

    def test_default_code_uri(self) -> None:
        config = ToolConfig()
        assert config.code_uri == ""

    def test_default_auth_type(self) -> None:
        config = ToolConfig()
        assert config.auth_type == "none"

    def test_default_auth_config(self) -> None:
        config = ToolConfig()
        assert config.auth_config == ()


@pytest.mark.unit
class TestToolConfigCustom:
    def test_mcp_server_config(self) -> None:
        config = ToolConfig(
            server_url="http://localhost:3000",
            transport="sse",
        )
        assert config.server_url == "http://localhost:3000"
        assert config.transport == "sse"

    def test_api_config(self) -> None:
        config = ToolConfig(
            endpoint_url="https://api.example.com/v1",
            method="GET",
            headers=(("Authorization", "Bearer token"),),
        )
        assert config.endpoint_url == "https://api.example.com/v1"
        assert config.method == "GET"
        assert config.headers == (("Authorization", "Bearer token"),)

    def test_function_config(self) -> None:
        config = ToolConfig(
            runtime="python3.12",
            handler="index.handler",
            code_uri="s3://bucket/code.zip",
        )
        assert config.runtime == "python3.12"
        assert config.handler == "index.handler"
        assert config.code_uri == "s3://bucket/code.zip"

    def test_auth_config(self) -> None:
        config = ToolConfig(
            auth_type="api_key",
            auth_config=(("key", "sk-xxx"),),
        )
        assert config.auth_type == "api_key"
        assert config.auth_config == (("key", "sk-xxx"),)


@pytest.mark.unit
class TestToolConfigImmutability:
    def test_frozen_cannot_set_server_url(self) -> None:
        config = ToolConfig()
        with pytest.raises(AttributeError):
            config.server_url = "http://new-url"  # type: ignore[misc]

    def test_frozen_cannot_set_transport(self) -> None:
        config = ToolConfig()
        with pytest.raises(AttributeError):
            config.transport = "sse"  # type: ignore[misc]


@pytest.mark.unit
class TestToolConfigEquality:
    def test_equal_configs(self) -> None:
        config1 = ToolConfig()
        config2 = ToolConfig()
        assert config1 == config2

    def test_different_configs(self) -> None:
        config1 = ToolConfig(server_url="http://a.com")
        config2 = ToolConfig(server_url="http://b.com")
        assert config1 != config2

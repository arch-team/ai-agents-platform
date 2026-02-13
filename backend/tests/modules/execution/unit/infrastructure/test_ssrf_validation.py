"""SSRF URL 验证测试。"""

import pytest

from src.modules.execution.infrastructure.external.claude_agent_adapter import (
    _validate_url,
)


@pytest.mark.unit
class TestValidateUrl:
    """_validate_url SSRF 防护测试。"""

    def test_allows_https_public_url(self) -> None:
        """允许 HTTPS 公共 URL。"""
        _validate_url("https://api.example.com/v1/data")

    def test_allows_http_public_url(self) -> None:
        """允许 HTTP 公共 URL。"""
        _validate_url("http://api.example.com/v1/data")

    def test_blocks_non_http_scheme(self) -> None:
        """禁止非 HTTP(S) 协议。"""
        with pytest.raises(ValueError, match="仅支持 HTTP/HTTPS 协议"):
            _validate_url("ftp://example.com/file")

    def test_blocks_file_scheme(self) -> None:
        """禁止 file:// 协议。"""
        with pytest.raises(ValueError, match="仅支持 HTTP/HTTPS 协议"):
            _validate_url("file:///etc/passwd")

    def test_blocks_metadata_endpoint(self) -> None:
        """禁止 AWS 元数据服务地址。"""
        with pytest.raises(ValueError, match="禁止访问内部地址"):
            _validate_url("http://169.254.169.254/latest/meta-data/")

    def test_blocks_google_metadata(self) -> None:
        """禁止 GCP 元数据服务地址。"""
        with pytest.raises(ValueError, match="禁止访问内部地址"):
            _validate_url("http://metadata.google.internal/computeMetadata/")

    def test_blocks_localhost(self) -> None:
        """禁止 localhost。"""
        with pytest.raises(ValueError, match="禁止访问内部地址"):
            _validate_url("http://localhost:8080/api")

    def test_blocks_loopback_127(self) -> None:
        """禁止 127.0.0.1。"""
        with pytest.raises(ValueError, match="禁止访问内部地址"):
            _validate_url("http://127.0.0.1:8080/api")

    def test_blocks_zero_address(self) -> None:
        """禁止 0.0.0.0。"""
        with pytest.raises(ValueError, match="禁止访问内部地址"):
            _validate_url("http://0.0.0.0:8080/api")

    def test_blocks_private_10_network(self) -> None:
        """禁止 10.x.x.x 内网地址。"""
        with pytest.raises(ValueError, match="禁止访问内网地址"):
            _validate_url("http://10.0.0.1:8080/api")

    def test_blocks_private_172_network(self) -> None:
        """禁止 172.16.x.x 内网地址。"""
        with pytest.raises(ValueError, match="禁止访问内网地址"):
            _validate_url("http://172.16.0.1:8080/api")

    def test_blocks_private_192_network(self) -> None:
        """禁止 192.168.x.x 内网地址。"""
        with pytest.raises(ValueError, match="禁止访问内网地址"):
            _validate_url("http://192.168.1.1:8080/api")

    def test_blocks_link_local_address(self) -> None:
        """禁止链路本地地址 169.254.x.x。"""
        with pytest.raises(ValueError, match="禁止访问内网地址"):
            _validate_url("http://169.254.1.1/")

    def test_allows_hostname_not_ip(self) -> None:
        """允许非 IP 的主机名（DNS 解析后再验证）。"""
        _validate_url("https://some-internal-service.company.com/api")

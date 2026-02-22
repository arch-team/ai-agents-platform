"""Builder 模块架构合规测试。"""

import ast
import pathlib

import pytest


_MODULE_ROOT = pathlib.Path(__file__).resolve().parents[4] / "src" / "modules" / "builder"
_FORBIDDEN_DOMAIN_IMPORTS = [
    "src.modules.agents.domain",
    "src.modules.auth.domain",
    "src.modules.evaluation.domain",
    "src.modules.execution.domain",
    "src.modules.insights.domain",
    "src.modules.knowledge.domain",
    "src.modules.templates.domain",
    "src.modules.tool_catalog.domain",
    "src.modules.audit.domain",
]


def _collect_imports(file_path: pathlib.Path) -> list[str]:
    """收集 Python 文件中的所有 import 路径。"""
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


@pytest.mark.unit
class TestBuilderArchitectureCompliance:
    """验证 builder 模块不直接导入其他模块的 domain 层。"""

    def test_domain_layer_does_not_import_other_modules(self) -> None:
        """builder/domain/ 不能导入其他模块。"""
        domain_dir = _MODULE_ROOT / "domain"
        if not domain_dir.exists():
            pytest.skip("builder/domain 目录不存在")

        violations: list[str] = []
        for py_file in domain_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            for imp in _collect_imports(py_file):
                for forbidden in _FORBIDDEN_DOMAIN_IMPORTS:
                    if imp.startswith(forbidden):
                        violations.append(f"{py_file.name}: {imp}")

        assert not violations, f"Domain 层违规导入: {violations}"

    def test_application_layer_does_not_import_other_domain(self) -> None:
        """builder/application/ 不能导入其他模块的 domain 层。"""
        app_dir = _MODULE_ROOT / "application"
        if not app_dir.exists():
            pytest.skip("builder/application 目录不存在")

        violations: list[str] = []
        for py_file in app_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            for imp in _collect_imports(py_file):
                for forbidden in _FORBIDDEN_DOMAIN_IMPORTS:
                    if imp.startswith(forbidden):
                        violations.append(f"{py_file.name}: {imp}")

        # 允许导入 agents 的 application 层（CreateAgentDTO, AgentService）
        # 但不允许导入其他模块的 domain 层
        assert not violations, f"Application 层违规导入其他模块 Domain: {violations}"

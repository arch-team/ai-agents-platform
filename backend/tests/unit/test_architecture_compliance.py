"""Architecture compliance tests.

Validates dependency direction, module isolation, and layer constraints
per architecture.md section 9.
"""

import ast
import pathlib

import pytest

from src.shared.api import (
    ErrorResponse,
    PageRequest,
    PageResponse,
    register_exception_handlers,
)
from src.shared.domain import (
    DomainError,
    DomainEvent,
    DuplicateEntityError,
    EntityNotFoundError,
    EventBus,
    InvalidStateTransitionError,
    IRepository,
    PydanticEntity,
    ResourceQuotaExceededError,
    ValidationError,
    event_bus,
    event_handler,
)
from src.shared.infrastructure import (
    Base,
    PydanticRepository,
    Settings,
    get_db,
    get_settings,
)


# 项目根目录
_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_SRC_ROOT = _BACKEND_ROOT / "src"


def _get_imports(file_path: pathlib.Path) -> list[str]:
    """Parse all import statements from a Python file."""
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _get_python_files(directory: pathlib.Path) -> list[pathlib.Path]:
    """Get all Python files in directory, excluding __init__.py and __pycache__."""
    if not directory.exists():
        return []
    return [
        f
        for f in directory.rglob("*.py")
        if f.name != "__init__.py" and "__pycache__" not in str(f)
    ]


# 禁止在 Domain 层出现的外部框架导入
_FORBIDDEN_DOMAIN_IMPORTS = [
    "fastapi",
    "sqlalchemy",
    "boto3",
    "botocore",
    "sagemaker",
    "uvicorn",
    "alembic",
    "httpx",
]


@pytest.mark.unit
class TestCleanArchitectureLayers:
    """Clean Architecture layer dependency direction tests."""

    def test_domain_layer_does_not_import_infrastructure(self):
        """Domain layer must not import Infrastructure layer."""
        domain_dirs = [
            _SRC_ROOT / "shared" / "domain",
            *(_SRC_ROOT / "modules").glob("*/domain"),
        ]
        for domain_dir in domain_dirs:
            for py_file in _get_python_files(domain_dir):
                imports = _get_imports(py_file)
                for imp in imports:
                    assert "infrastructure" not in imp, (
                        f"{py_file.relative_to(_BACKEND_ROOT)} "
                        f"imports infrastructure: {imp}"
                    )

    def test_domain_layer_does_not_import_presentation(self):
        """Domain layer must not import Presentation layer."""
        domain_dirs = [
            _SRC_ROOT / "shared" / "domain",
            *(_SRC_ROOT / "modules").glob("*/domain"),
        ]
        for domain_dir in domain_dirs:
            for py_file in _get_python_files(domain_dir):
                imports = _get_imports(py_file)
                for imp in imports:
                    assert "presentation" not in imp, (
                        f"{py_file.relative_to(_BACKEND_ROOT)} "
                        f"imports presentation layer: {imp}"
                    )

    def test_domain_layer_does_not_import_api(self):
        """Domain layer must not import API layer."""
        domain_dirs = [
            _SRC_ROOT / "shared" / "domain",
            *(_SRC_ROOT / "modules").glob("*/domain"),
        ]
        for domain_dir in domain_dirs:
            for py_file in _get_python_files(domain_dir):
                imports = _get_imports(py_file)
                for imp in imports:
                    parts = imp.split(".")
                    assert "api" not in parts[:2], (
                        f"{py_file.relative_to(_BACKEND_ROOT)} "
                        f"imports API layer: {imp}"
                    )

    def test_domain_layer_does_not_import_application(self):
        """Domain layer must not import Application layer."""
        domain_dirs = [
            _SRC_ROOT / "shared" / "domain",
            *(_SRC_ROOT / "modules").glob("*/domain"),
        ]
        for domain_dir in domain_dirs:
            for py_file in _get_python_files(domain_dir):
                imports = _get_imports(py_file)
                for imp in imports:
                    assert ".application." not in imp, (
                        f"{py_file.relative_to(_BACKEND_ROOT)} "
                        f"imports application layer: {imp}"
                    )


@pytest.mark.unit
class TestModuleDomainLayerIsolation:
    """Module Domain layer isolation tests (R1)."""

    def test_domain_no_forbidden_framework_imports(self):
        """Domain layer must not import external frameworks."""
        domain_dirs = [
            _SRC_ROOT / "shared" / "domain",
            *(_SRC_ROOT / "modules").glob("*/domain"),
        ]
        for domain_dir in domain_dirs:
            for py_file in _get_python_files(domain_dir):
                imports = _get_imports(py_file)
                for imp in imports:
                    root_module = imp.split(".")[0]
                    assert root_module not in _FORBIDDEN_DOMAIN_IMPORTS, (
                        f"{py_file.relative_to(_BACKEND_ROOT)} "
                        f"imports forbidden framework: {imp}"
                    )

    def test_module_domain_does_not_import_other_module(self):
        """Module Domain must not import other modules (R1)."""
        modules_dir = _SRC_ROOT / "modules"
        if not modules_dir.exists():
            pytest.skip("modules directory does not exist")

        for module_dir in modules_dir.iterdir():
            if not module_dir.is_dir() or module_dir.name.startswith("_"):
                continue
            module_name = module_dir.name
            domain_dir = module_dir / "domain"
            for py_file in _get_python_files(domain_dir):
                imports = _get_imports(py_file)
                for imp in imports:
                    if imp.startswith("src.modules."):
                        imported_module = imp.split(".")[2]
                        assert imported_module == module_name, (
                            f"{py_file.relative_to(_BACKEND_ROOT)} "
                            f"imports other module: {imp}"
                        )

    def test_shared_domain_has_no_business_logic_imports(self):
        """shared/domain must not import business modules."""
        shared_domain = _SRC_ROOT / "shared" / "domain"
        for py_file in _get_python_files(shared_domain):
            imports = _get_imports(py_file)
            for imp in imports:
                assert not imp.startswith("src.modules."), (
                    f"{py_file.relative_to(_BACKEND_ROOT)} "
                    f"imports business module: {imp}"
                )


@pytest.mark.unit
class TestModuleApplicationLayerDependencies:
    """Module Application layer dependency tests (R2)."""

    def test_application_does_not_import_infrastructure(self):
        """Application layer must not import Infrastructure."""
        app_dirs = list((_SRC_ROOT / "modules").glob("*/application"))
        for app_dir in app_dirs:
            for py_file in _get_python_files(app_dir):
                imports = _get_imports(py_file)
                for imp in imports:
                    assert ".infrastructure." not in imp, (
                        f"{py_file.relative_to(_BACKEND_ROOT)} "
                        f"imports infrastructure: {imp}"
                    )

    def test_application_does_not_import_presentation(self):
        """Application layer must not import Presentation layer."""
        app_dirs = list((_SRC_ROOT / "modules").glob("*/application"))
        for app_dir in app_dirs:
            for py_file in _get_python_files(app_dir):
                imports = _get_imports(py_file)
                for imp in imports:
                    assert ".api." not in imp, (
                        f"{py_file.relative_to(_BACKEND_ROOT)} "
                        f"imports API layer: {imp}"
                    )
                    assert "presentation" not in imp, (
                        f"{py_file.relative_to(_BACKEND_ROOT)} "
                        f"imports presentation layer: {imp}"
                    )


@pytest.mark.unit
class TestModuleApiLayerAuthDependency:
    """API layer auth dependency exception test (R4)."""

    def test_api_layer_does_not_import_other_module_internals(self):
        """API layer must not import other module internals (auth exception)."""
        modules_dir = _SRC_ROOT / "modules"
        if not modules_dir.exists():
            pytest.skip("modules directory does not exist")

        for module_dir in modules_dir.iterdir():
            if not module_dir.is_dir() or module_dir.name.startswith("_"):
                continue
            module_name = module_dir.name
            api_dir = module_dir / "api"
            for py_file in _get_python_files(api_dir):
                imports = _get_imports(py_file)
                for imp in imports:
                    if imp.startswith("src.modules."):
                        imported_module = imp.split(".")[2]
                        assert imported_module in (module_name, "auth"), (
                            f"{py_file.relative_to(_BACKEND_ROOT)} "
                            f"imports other module: {imp}"
                        )


@pytest.mark.unit
class TestCrossModuleCommunication:
    """Cross-module communication rules (R3)."""

    def test_no_circular_module_dependencies(self):
        """No circular dependencies between modules."""
        modules_dir = _SRC_ROOT / "modules"
        if not modules_dir.exists():
            pytest.skip("modules directory does not exist")

        # 收集每个模块依赖的其他模块
        deps: dict[str, set[str]] = {}
        for module_dir in modules_dir.iterdir():
            if not module_dir.is_dir() or module_dir.name.startswith("_"):
                continue
            module_name = module_dir.name
            deps[module_name] = set()
            for py_file in _get_python_files(module_dir):
                imports = _get_imports(py_file)
                for imp in imports:
                    if imp.startswith("src.modules."):
                        imported_module = imp.split(".")[2]
                        if imported_module != module_name:
                            deps[module_name].add(imported_module)

        # 检测双向依赖
        for module_a, module_a_deps in deps.items():
            for module_b in module_a_deps:
                if module_b in deps:
                    assert module_a not in deps[module_b], (
                        f"Circular dependency: {module_a} <-> {module_b}"
                    )


@pytest.mark.unit
class TestSharedModuleExports:
    """shared module __init__.py export completeness tests."""

    def test_shared_domain_exports(self):
        """shared/domain exports all core classes."""
        assert PydanticEntity is not None
        assert IRepository is not None
        assert DomainError is not None
        assert DomainEvent is not None
        assert EventBus is not None
        assert event_bus is not None
        assert event_handler is not None
        assert EntityNotFoundError is not None
        assert DuplicateEntityError is not None
        assert InvalidStateTransitionError is not None
        assert ValidationError is not None
        assert ResourceQuotaExceededError is not None

    def test_shared_api_exports(self):
        """shared/api exports all core classes."""
        assert ErrorResponse is not None
        assert PageRequest is not None
        assert PageResponse is not None
        assert register_exception_handlers is not None

    def test_shared_infrastructure_exports(self):
        """shared/infrastructure exports all core classes."""
        assert Base is not None
        assert PydanticRepository is not None
        assert Settings is not None
        assert get_db is not None
        assert get_settings is not None

"""预置 Agent 模板独立运行 seed 脚本。

使用方式:
    uv run python -m scripts.seed_templates

种子数据常量定义在 src/modules/templates/domain/seed_data.py，
应用启动时也会通过 lifespan 自动 seed（幂等）。
"""

from src.modules.templates.domain.seed_data import SEED_TEMPLATES


__all__ = ["SEED_TEMPLATES"]

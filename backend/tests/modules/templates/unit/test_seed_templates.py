"""预置模板种子数据完整性测试。"""

import pytest

from scripts.seed_templates import SEED_TEMPLATES
from src.modules.templates.domain.value_objects.template_category import (
    TemplateCategory,
)
from src.modules.templates.domain.value_objects.template_config import TemplateConfig


@pytest.mark.unit
class TestSeedTemplates:
    """预置模板种子数据完整性测试。"""

    def test_has_16_templates(self) -> None:
        assert len(SEED_TEMPLATES) == 16

    def test_all_have_required_fields(self) -> None:
        required_fields = {
            "name",
            "description",
            "category",
            "tags",
            "system_prompt",
            "model_id",
            "temperature",
            "max_tokens",
            "is_featured",
        }
        for i, t in enumerate(SEED_TEMPLATES):
            missing = required_fields - set(t.keys())
            assert not missing, f"模板 #{i + 1} 缺少字段: {missing}"

    def test_categories_are_valid(self) -> None:
        for t in SEED_TEMPLATES:
            assert isinstance(t["category"], TemplateCategory), f"{t['name']} 分类无效"

    def test_names_unique(self) -> None:
        names = [str(t["name"]) for t in SEED_TEMPLATES]
        assert len(names) == len(set(names)), "存在重复名称"

    def test_featured_count(self) -> None:
        featured = [t for t in SEED_TEMPLATES if t["is_featured"]]
        assert len(featured) == 7

    def test_configs_valid(self) -> None:
        for t in SEED_TEMPLATES:
            config = TemplateConfig(
                system_prompt=str(t["system_prompt"]),
                model_id=str(t["model_id"]),
                temperature=float(str(t["temperature"])),
                max_tokens=int(str(t["max_tokens"])),
            )
            assert config.system_prompt, f"{t['name']} 缺少 system_prompt"

    def test_all_categories_covered(self) -> None:
        categories = {t["category"] for t in SEED_TEMPLATES}
        expected = {
            TemplateCategory.CUSTOMER_SERVICE,
            TemplateCategory.CODE_ASSISTANT,
            TemplateCategory.DATA_ANALYSIS,
            TemplateCategory.CONTENT_CREATION,
            TemplateCategory.RESEARCH,
            TemplateCategory.WORKFLOW_AUTOMATION,
        }
        assert expected.issubset(categories), f"缺少分类: {expected - categories}"

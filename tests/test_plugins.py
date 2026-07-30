from plugins.fashion.validator import FashionValidator as PluginFashionValidator
from plugins.registry import ValidatorRegistry
from validators.fashion import FashionValidator as LegacyFashionValidator


def test_registry_discovers_plugin_and_legacy_validators() -> None:
    registry = ValidatorRegistry()
    assert registry.categories() == ["Cosmetics", "Fashion", "HomeAppliances"]
    assert isinstance(registry.get("Fashion"), PluginFashionValidator)


def test_legacy_fashion_import_remains_compatible() -> None:
    assert LegacyFashionValidator is PluginFashionValidator

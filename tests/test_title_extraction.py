import pandas as pd
from domain.catalog.title_extraction import extract_product_attributes
from validators.home_appliances import HomeAppliancesValidator


def test_extracts_requested_home_appliance_fields() -> None:
    item = extract_product_attributes("Teckwe CS-1000 Portable Silicone Air Fryer Liners, 12.7QT, Pink")
    assert item.brand == "Teckwe"
    assert item.model_series == "CS-1000"
    assert item.products == "Air Fryer Liners + Air Fryer"
    assert item.material == "Silicone"
    assert item.spec == "12.7QT"
    assert item.standard_title() == "Teckwe CS-1000 Air Fryer Liners + Air Fryer Pink + Portable Silicone (12.7QT)"


def test_enrichment_marks_second_canonical_duplicate() -> None:
    frame = pd.DataFrame({"product_title": ["Teckwe CS-1000 Air Fryer, Silicone, 500W", "Teckwe CS-1000 Air Fryer, Silicone, 500W"]})
    validator = HomeAppliancesValidator(); enriched = validator.autofix(frame)
    assert list(enriched.columns[-7:]) == ["Brands", "Model_Series", "Products", "Material", "Spec", "Attribute_Special", "standard_title"]
    assert [issue.code for issue in validator.validate(enriched, {})] == ["duplicate_product"]


def test_distinct_source_titles_are_not_merged_by_same_canonical_title() -> None:
    frame = pd.DataFrame({"product_title": ["Portable Mini Fan with lanyard", "Portable Mini Fan with desk stand"]})
    validator = HomeAppliancesValidator()
    assert validator.validate(validator.autofix(frame), {}) == []


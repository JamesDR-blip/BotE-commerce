import pandas as pd

from agents.extraction import ExtractionAgent
from extractors.base import ExtractedAttributes
from extractors.deterministic import DeterministicProductExtractor


def test_deterministic_extractor_supports_all_requested_attributes() -> None:
    item = DeterministicProductExtractor().extract(
        "Philips Model HX-200 Blue XL Stainless Steel 1.5kg 220V 2L SKU: AB-123 UPC: 123456789012 GTIN: 12345678901234"
    )
    assert item == ExtractedAttributes(
        brand="Philips", model="HX-200", color="Blue", size="XL", weight="1.5kg", material="Stainless Steel",
        voltage="220V", capacity="2L", sku="AB-123", upc="123456789012", gtin="12345678901234",
    )


def test_extraction_agent_is_read_only_and_accepts_title_aliases() -> None:
    frame = pd.DataFrame({"title": ["Xiaomi Fan 5V"]})
    extracted = ExtractionAgent(DeterministicProductExtractor()).extract(frame)
    assert extracted[0].brand == "Xiaomi"
    assert list(frame.columns) == ["title"]


def test_extraction_agent_returns_no_records_without_a_title_column() -> None:
    assert ExtractionAgent(DeterministicProductExtractor()).extract(pd.DataFrame({"sku": ["A-1"]})) == []

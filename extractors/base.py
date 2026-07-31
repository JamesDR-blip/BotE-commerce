"""Framework-independent contracts for product attribute extraction."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExtractedAttributes:
    brand: str = ""
    model: str = ""
    color: str = ""
    size: str = ""
    weight: str = ""
    material: str = ""
    voltage: str = ""
    capacity: str = ""
    sku: str = ""
    upc: str = ""
    gtin: str = ""

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


class ProductExtractor(Protocol):
    """Extract attributes from unstructured product text without mutating it."""

    def extract(self, value: object) -> ExtractedAttributes: ...

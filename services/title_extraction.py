"""Backward-compatible import for domain catalog primitives."""
from domain.catalog.title_extraction import (
    COLORS,
    FEATURES,
    KNOWN_BRANDS,
    MATERIALS,
    PRODUCT_PATTERNS,
    SPEC_PATTERN,
    ProductAttributes,
    extract_product_attributes,
)

__all__ = [
    "COLORS",
    "FEATURES",
    "KNOWN_BRANDS",
    "MATERIALS",
    "PRODUCT_PATTERNS",
    "SPEC_PATTERN",
    "ProductAttributes",
    "extract_product_attributes",
]

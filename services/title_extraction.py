"""Deterministic product-title enrichment for home-appliance feeds.

The extractor is intentionally rule based: outputs are explainable and never
depend on generated code or an LLM.  Vocabulary can be extended safely as new
catalogue data is observed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


KNOWN_BRANDS = {"Teckwe", "Kemei", "Wit", "Ninja", "Philips", "Xiaomi", "Dyson", "Keurig", "Cosori", "Instant"}
MATERIALS = ("Silicone", "Stainless Steel", "Plastic", "Glass", "Ceramic", "Aluminum", "Metal", "Bamboo", "Rubber")
COLORS = ("Black", "White", "Pink", "Red", "Blue", "Green", "Purple", "Silver", "Gold", "Grey", "Gray", "Colored")
FEATURES = ("Rechargeable", "Portable", "Cordless", "Waterproof", "Wireless", "Bluetooth", "Mini", "Compact", "Handheld", "Smart", "Multi-Functional", "Ultra-Silent", "Electric", "Battery Operated")
PRODUCT_PATTERNS = (
    "Air Fryer Liners", "Air Fryer", "Massage Gun", "Neck Fan", "Handheld Fan", "Mini Fan", "Water Flosser", "Oral Irrigator", "Electric Toothbrush", "Ice Pop Mold", "Thermal Printer", "Air Humidifier", "Epilator", "Electric Trimmer", "Eyelash Curler", "Ice Cream Mold",
)
SPEC_PATTERN = re.compile(r"\b(?:\d+(?:\.\d+)?\s*(?:W|kW|mAh|V|Hz|QT|L|ML|oz|cm|mm)|\d+\s*(?:AA|AAA)\s*(?:Batter(?:y|ies))?)\b", re.IGNORECASE)


@dataclass(frozen=True)
class ProductAttributes:
    brand: str = ""
    model_series: str = ""
    products: str = ""
    material: str = ""
    spec: str = ""
    attribute_special: str = ""

    def standard_title(self) -> str:
        """Build the requested canonical title, skipping unavailable fields."""
        return " ".join(part for part in (self.brand, self.model_series, self.products, self.attribute_special, self.material, f"({self.spec})" if self.spec else "") if part).strip()


def _matches(text: str, choices: tuple[str, ...]) -> list[str]:
    return [item for item in choices if re.search(rf"\b{re.escape(item)}\b", text, re.IGNORECASE)]


def extract_product_attributes(value: object) -> ProductAttributes:
    """Extract catalogue fields from one unstructured product title."""
    title = re.sub(r"\s+", " ", str(value or "")).strip()
    brand = next((name for name in KNOWN_BRANDS if re.search(rf"\b{re.escape(name)}\b", title, re.IGNORECASE)), "")
    # Explicit model codes (CS-1000, KM-123) and named series (Foodi®).
    model = re.search(r"\b[A-Za-z]{1,8}[-_]\d{2,}\b|\b(?:Foodi)®?\b", title, re.IGNORECASE)
    products = _matches(title, PRODUCT_PATTERNS)
    materials = _matches(title, MATERIALS)
    attributes = _matches(title, COLORS) + _matches(title, FEATURES)
    specs = SPEC_PATTERN.findall(title)
    return ProductAttributes(
        brand=brand,
        model_series=model.group(0) if model else "",
        products=" + ".join(dict.fromkeys(products)),
        material=" + ".join(dict.fromkeys(materials)),
        spec=" + ".join(dict.fromkeys(specs)),
        attribute_special=" + ".join(dict.fromkeys(attributes)),
    )

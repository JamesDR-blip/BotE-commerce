"""Explainable, regex-based product attribute extraction."""
from __future__ import annotations

import re

from services.title_extraction import COLORS, KNOWN_BRANDS, MATERIALS

from .base import ExtractedAttributes


def _first_choice(text: str, choices: tuple[str, ...] | set[str]) -> str:
    return next((choice for choice in choices if re.search(rf"\b{re.escape(choice)}\b", text, re.IGNORECASE)), "")


def _first_match(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


class DeterministicProductExtractor:
    """Extract a fixed ecommerce attribute set using reviewed patterns only."""

    def extract(self, value: object) -> ExtractedAttributes:
        text = re.sub(r"\s+", " ", str(value or "")).strip()
        model = _first_match(text, r"\b([A-Za-z]{1,8}[-_]\d{2,})\b") or _first_match(
            text, r"\b(?:Model|Series)\s+([A-Za-z0-9-]+)\b"
        )
        return ExtractedAttributes(
            brand=_first_choice(text, KNOWN_BRANDS),
            model=model,
            color=_first_choice(text, COLORS),
            size=_first_match(text, r"\b(XXS|XS|S|M|L|XL|XXL|XXXL|\d+(?:\.\d+)?\s*(?:cm|mm|in|inch(?:es)?))\b"),
            weight=_first_match(text, r"\b(\d+(?:\.\d+)?\s*(?:kg|g|lb|lbs|oz))\b"),
            material=_first_choice(text, MATERIALS),
            voltage=_first_match(text, r"\b(\d+(?:\.\d+)?\s*(?:V|volt(?:s)?))\b"),
            capacity=_first_match(text, r"\b(\d+(?:\.\d+)?\s*(?:mAh|L|ML|oz|QT|gal))\b"),
            sku=_first_match(text, r"\b(?:SKU|Item(?:\s*(?:No|Number))?|Code)\s*[:#-]?\s*([A-Za-z0-9][A-Za-z0-9_-]{2,})\b"),
            upc=_first_match(text, r"\bUPC\s*[:#-]?\s*(\d{12})\b"),
            gtin=_first_match(text, r"\bGTIN\s*[:#-]?\s*(\d{8}|\d{12,14})\b"),
        )

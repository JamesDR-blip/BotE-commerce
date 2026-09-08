"""Deterministic, non-mutating column mapping suggestions."""
from __future__ import annotations

import re
from collections.abc import Iterable


class MappingService:
    """Suggest canonical ecommerce fields from familiar source column aliases."""

    _ALIASES = {
        "brand": ("brand", "brands", "manufacturer", "maker"),
        "model": ("model", "model_number", "model_series"),
        "color": ("color", "colour"),
        "size": ("size", "dimension", "dimensions"),
        "weight": ("weight", "item_weight"),
        "material": ("material", "fabric"),
        "voltage": ("voltage", "volt"),
        "capacity": ("capacity", "volume"),
        "sku": ("sku", "seller_sku", "item_sku"),
        "upc": ("upc",),
        "gtin": ("gtin", "ean", "barcode"),
        "product_title": ("product_title", "title", "name", "product_name"),
        "price": ("price", "sale_price", "regular_price"),
    }

    @staticmethod
    def _normalise(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.casefold())

    def suggest(self, columns: Iterable[object], target_columns: Iterable[str] | None = None) -> tuple[dict[str, str], list[str]]:
        allowed = set(target_columns or self._ALIASES)
        aliases = {
            self._normalise(alias): canonical
            for canonical, values in self._ALIASES.items()
            if canonical in allowed
            for alias in values
        }
        mappings: dict[str, str] = {}
        unmapped: list[str] = []
        for column in columns:
            source = str(column)
            target = aliases.get(self._normalise(source))
            if target:
                mappings[source] = target
            else:
                unmapped.append(source)
        return mappings, unmapped

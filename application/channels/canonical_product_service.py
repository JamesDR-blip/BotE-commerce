"""Application service for deterministic dataset-to-canonical-product projection."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd

from domain.catalog.mapping import MappingService
from domain.catalog.normalization import NormalizationService
from domain.channel_sync import CanonicalProduct
from domain.identity import CurrentUser
from infrastructure.storage.dataset_storage import DatasetStorage
from infrastructure.upload.tabular_reader import TabularUploadReader
from repositories.datasets import DatasetRepository


class CanonicalProductService:
    """Project an owned dataset into deterministic canonical products.

    This service is intentionally read-only. It does not mutate datasets,
    create ChangeSets, or persist product records.
    """

    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        storage: DatasetStorage,
        reader: TabularUploadReader,
        mapping: MappingService,
        normalization: NormalizationService,
    ) -> None:
        self._datasets = datasets
        self._storage = storage
        self._reader = reader
        self._mapping = mapping
        self._normalization = normalization

    def project_dataset(
        self,
        *,
        dataset_id: str,
        current_user: CurrentUser,
    ) -> list[CanonicalProduct]:
        dataset = self._datasets.get_for_owner(
            dataset_id=dataset_id,
            owner_id=current_user.user_id,
        )

        if dataset is None:
            raise ValueError(f"Dataset not found: {dataset_id}")

        if not dataset.storage_key:
            raise ValueError(
                f"Dataset has no persisted source: {dataset_id}"
            )

        if not dataset.filename:
            raise ValueError(
                f"Dataset has no source filename: {dataset_id}"
            )

        with self._storage.open(storage_key=dataset.storage_key) as source:
            content = source.read()

        frame = self._reader.read(
            filename=dataset.filename,
            content=content,
        )

        return self.project_frame(frame)

    def project_frame(
        self,
        frame: pd.DataFrame,
    ) -> list[CanonicalProduct]:
        """Project a tabular frame without mutating the input frame."""

        if frame.empty:
            return []

        mappings, _ = self._mapping.suggest(
            frame.columns,
            target_columns={
                "brand",
                "sku",
                "product_title",
                "price",
            },
        )

        canonical = frame.rename(columns=mappings).copy(deep=True)

        normalization_fields = [
            field
            for field in ("product_title",)
            if field in canonical.columns
        ]

        if normalization_fields:
            canonical = self._normalization.normalize(
                canonical,
                fields=normalization_fields,
            )

        if "product_title" not in canonical.columns:
            raise ValueError(
                "Dataset must contain a product title column"
            )

        products: list[CanonicalProduct] = []
        seen_product_ids: set[str] = set()

        for _, row in canonical.iterrows():
            product = self._to_product(row)

            if product.product_id in seen_product_ids:
                raise ValueError(
                    "Dataset contains duplicate canonical product identity: "
                    f"{product.product_id}"
                )

            seen_product_ids.add(product.product_id)
            products.append(product)

        return products

    def _to_product(self, row: pd.Series) -> CanonicalProduct:
        title = self._text(row.get("product_title"))
        sku = self._text(row.get("sku"))
        brand = self._text(row.get("brand"))
        price = self._price(row.get("price"))

        product_id = sku or self._identity(
            title=title,
            brand=brand,
            attributes={},
        )

        return CanonicalProduct(
            product_id=product_id,
            title=title,
            sku=sku,
            brand=brand,
            price=price,
            attributes={},
        )

    @staticmethod
    def _text(value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, float) and pd.isna(value):
            return ""

        return str(value).strip()

    @classmethod
    def _price(cls, value: Any) -> str:
        text = cls._text(value)
        if not text:
            return ""

        try:
            return str(Decimal(text))
        except InvalidOperation:
            return text

    @staticmethod
    def _identity(
        *,
        title: str,
        brand: str,
        attributes: dict[str, Any],
    ) -> str:
        identity_payload = {
            "title": title,
            "brand": brand,
            "attributes": attributes,
        }

        canonical = json.dumps(
            identity_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return "product-" + hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()


__all__ = ["CanonicalProductService"]

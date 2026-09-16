import pandas as pd
import pytest

from application.channels.canonical_product_service import (
    CanonicalProductService,
)
from domain.catalog.mapping import MappingService
from domain.catalog.normalization import NormalizationService
from infrastructure.storage.dataset_storage import DatasetStorage
from infrastructure.upload.tabular_reader import TabularUploadReader


def make_service(tmp_path):
    from repositories.datasets import DatasetRepository

    class FakeDatasets:
        def __init__(self):
            self.dataset = None

        def get_for_owner(self, *, dataset_id, owner_id):
            if self.dataset is None:
                return None
            if self.dataset.id != dataset_id:
                return None
            if self.dataset.project_id != "project-1":
                return None
            return self.dataset

    return CanonicalProductService(
        datasets=FakeDatasets(),
        storage=DatasetStorage(tmp_path),
        reader=TabularUploadReader(max_bytes=1024 * 1024),
        mapping=MappingService(),
        normalization=NormalizationService(),
    )


def test_project_frame_maps_and_normalizes_canonical_fields(tmp_path):
    service = make_service(tmp_path)

    frame = pd.DataFrame(
        [
            {
                "SKU": "SKU-1",
                "Title": "  Red   Shirt  ",
                "Brand": " Acme ",
                "Price": 100,
            }
        ]
    )

    products = service.project_frame(frame)

    assert len(products) == 1
    assert products[0].product_id == "SKU-1"
    assert products[0].title == "Red Shirt"
    assert products[0].sku == "SKU-1"
    assert products[0].brand == "Acme"
    assert products[0].price == "100"


def test_project_frame_does_not_mutate_input(tmp_path):
    service = make_service(tmp_path)

    frame = pd.DataFrame(
        [{"sku": "SKU-1", "title": "  Shirt  "}]
    )
    original = frame.copy(deep=True)

    service.project_frame(frame)

    pd.testing.assert_frame_equal(frame, original)


def test_project_frame_requires_title(tmp_path):
    service = make_service(tmp_path)

    with pytest.raises(
        ValueError,
        match="product title column",
    ):
        service.project_frame(
            pd.DataFrame([{"sku": "SKU-1"}])
        )


def test_project_frame_keeps_sku_identity_stable_when_price_changes(tmp_path):
    service = make_service(tmp_path)

    first = service.project_frame(
        pd.DataFrame(
            [
                {
                    "sku": "SKU-1",
                    "title": "Shirt",
                    "price": "100.00",
                }
            ]
        )
    )

    second = service.project_frame(
        pd.DataFrame(
            [
                {
                    "sku": "SKU-1",
                    "title": "Shirt Updated",
                    "price": "200.00",
                }
            ]
        )
    )

    assert first[0].product_id == "SKU-1"
    assert second[0].product_id == "SKU-1"
    assert first[0].price == "100.00"
    assert second[0].price == "200.00"


def test_project_frame_keeps_non_sku_identity_stable_when_price_changes(tmp_path):
    service = make_service(tmp_path)

    first = service.project_frame(
        pd.DataFrame(
            [
                {
                    "title": "Shirt",
                    "brand": "Acme",
                    "price": "100",
                }
            ]
        )
    )

    second = service.project_frame(
        pd.DataFrame(
            [
                {
                    "title": "Shirt",
                    "brand": "Acme",
                    "price": "200",
                }
            ]
        )
    )

    assert first[0].product_id == second[0].product_id

def test_project_frame_uses_deterministic_content_identity_without_sku(
    tmp_path,
):
    service = make_service(tmp_path)

    frame = pd.DataFrame(
        [
            {
                "title": "Shirt",
                "brand": "Acme",
                "price": "100.00",
            }
        ]
    )

    first = service.project_frame(frame)
    second = service.project_frame(frame.copy(deep=True))

    assert first[0].product_id == second[0].product_id
    assert first[0].product_id.startswith("product-")
    assert len(first[0].product_id) == len("product-") + 64


def test_project_frame_changes_price_without_changing_identity(tmp_path):
    service = make_service(tmp_path)

    first = service.project_frame(
        pd.DataFrame([{"title": "Shirt", "brand": "Acme", "price": "100"}])
    )
    second = service.project_frame(
        pd.DataFrame([{"title": "Shirt", "brand": "Acme", "price": "200"}])
    )

    assert first[0].product_id == second[0].product_id

def test_project_frame_rejects_duplicate_sku_identity(tmp_path):
    service = make_service(tmp_path)

    with pytest.raises(
        ValueError,
        match="duplicate canonical product identity",
    ):
        service.project_frame(
            pd.DataFrame(
                [
                    {"sku": "SKU-1", "title": "Shirt"},
                    {"sku": "SKU-1", "title": "Pants"},
                ]
            )
        )


def test_project_dataset_reads_owned_persisted_source(tmp_path):
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class Dataset:
        id: str
        project_id: str
        filename: str
        storage_key: str

    class FakeDatasets:
        def __init__(self, dataset):
            self.dataset = dataset

        def get_for_owner(self, *, dataset_id, owner_id):
            if dataset_id != self.dataset.id:
                return None
            return self.dataset

    storage = DatasetStorage(tmp_path)
    content = b"sku,title,brand,price\nSKU-1,Shirt,Acme,100\n"
    storage.save(
        storage_key="dataset-1.csv",
        content=content,
    )

    service = CanonicalProductService(
        datasets=FakeDatasets(
            Dataset(
                id="dataset-1",
                project_id="project-1",
                filename="catalog.csv",
                storage_key="dataset-1.csv",
            )
        ),
        storage=storage,
        reader=TabularUploadReader(max_bytes=1024 * 1024),
        mapping=MappingService(),
        normalization=NormalizationService(),
    )

    class User:
        user_id = "user-1"

    products = service.project_dataset(
        dataset_id="dataset-1",
        current_user=User(),
    )

    assert products[0].product_id == "SKU-1"
    assert products[0].title == "Shirt"


def test_project_dataset_rejects_unowned_dataset(tmp_path):
    class FakeDatasets:
        def get_for_owner(self, *, dataset_id, owner_id):
            return None

    service = CanonicalProductService(
        datasets=FakeDatasets(),
        storage=DatasetStorage(tmp_path),
        reader=TabularUploadReader(max_bytes=1024 * 1024),
        mapping=MappingService(),
        normalization=NormalizationService(),
    )

    class User:
        user_id = "user-1"

    with pytest.raises(
        ValueError,
        match="Dataset not found",
    ):
        service.project_dataset(
            dataset_id="dataset-1",
            current_user=User(),
        )

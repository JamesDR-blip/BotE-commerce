from domain.catalog.mapping import MappingService


def test_mapping_service_suggests_normalised_aliases() -> None:
    mappings, unmapped = MappingService().suggest(["Product Name", "Colour", "Seller SKU", "Unrelated"])
    assert mappings == {"Product Name": "product_title", "Colour": "color", "Seller SKU": "sku"}
    assert unmapped == ["Unrelated"]


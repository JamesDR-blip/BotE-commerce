from domain.capabilities import CapabilitySpec
from domain.capability_catalog import build_capability_catalog


def make_spec(capability_id: str) -> CapabilitySpec:
    return CapabilitySpec(
        id=capability_id,
        version="1.0",
        description=f"{capability_id} capability",
        input_keys=(),
        output_keys=(),
    )


def test_build_capability_catalog_indexes_specs_by_id():
    clean = make_spec("data.clean")
    validate = make_spec("data.validate")

    catalog = build_capability_catalog(
        (clean, validate)
    )

    assert catalog["data.clean"] is clean
    assert catalog["data.validate"] is validate


def test_build_capability_catalog_returns_empty_catalog_for_no_specs():
    catalog = build_capability_catalog(())

    assert catalog == {}
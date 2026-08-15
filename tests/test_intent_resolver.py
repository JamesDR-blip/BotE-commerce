from domain.intent_resolver import IntentResolver


def test_intent_resolves_capabilities():

    resolver = IntentResolver(
        {
            "clean_product_data": (
                "data.clean",
            ),
            "extract_product_attributes": (
                "data.extract",
            ),
        }
    )

    result = resolver.resolve(
        (
            "clean_product_data",
            "extract_product_attributes",
        )
    )

    assert result == (
        "data.clean",
        "data.extract",
    )


import pytest

from domain.intent_resolver import IntentResolver


def test_unknown_intent_is_rejected():

    resolver = IntentResolver(
        {
            "clean_product_data": (
                "data.clean",
            ),
        }
    )

    with pytest.raises(ValueError):
        resolver.resolve(
            (
                "unknown_intent",
            )
        )


def test_intent_resolution_deduplicates_capabilities():

    resolver = IntentResolver(
        {
            "clean_product_data": (
                "data.clean",
            ),
            "prepare_product_data": (
                "data.clean",
                "data.normalize",
            ),
        }
    )

    result = resolver.resolve(
        (
            "clean_product_data",
            "prepare_product_data",
        )
    )

    assert result == (
        "data.clean",
        "data.normalize",
    )
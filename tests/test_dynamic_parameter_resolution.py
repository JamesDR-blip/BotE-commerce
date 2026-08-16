from agents.parameter_resolver import ParameterResolver
from domain.capabilities import CapabilitySpec


def test_parameter_resolver_is_metadata_driven():

    resolver = ParameterResolver()

    catalog = {
        "custom.capability": CapabilitySpec(
            id="custom.capability",
            version="1.0",
            description="Custom capability",
            input_keys=("frame",),
            output_keys=("result",),
            parameter_keys=(
                "fields",
            ),
            parameter_keywords={
                "fields": {
                    "sku": (
                        "sku",
                        "mã sản phẩm",
                    ),
                    "price": (
                        "price",
                        "giá",
                    ),
                }
            },
        )
    }

    result = resolver.resolve(
        text="extract sku and price",
        capabilities=(
            "custom.capability",
        ),
        catalog=catalog,
    )

    assert result == {
        "custom.capability": {
            "fields": [
                "sku",
                "price",
            ]
        }
    }
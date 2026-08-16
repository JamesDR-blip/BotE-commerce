from agents.parameter_resolver import ParameterResolver

from domain.capabilities import CapabilitySpec


def test_parameter_resolver_extracts_attributes():

    resolver = ParameterResolver()

    catalog = {
        "data.extract": CapabilitySpec(
            id="data.extract",
            version="1.0",
            description="Extract",
            input_keys=(
                "frame",
            ),
            output_keys=(
                "extractions",
            ),
            parameter_keys=(
                "attributes",
            ),
        )
    }


    parameters = resolver.resolve(
        text="extract brand and model from product title",
        capabilities=(
            "data.extract",
        ),
        catalog=catalog,
    )


    assert parameters == {
        "data.extract": {
            "attributes": [
                "brand",
                "model",
            ]
        }
    }
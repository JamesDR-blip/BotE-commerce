from __future__ import annotations

from typing import Mapping

from domain.capabilities import CapabilitySpec


class ParameterResolver:
    """
    Resolve capability parameters from user intent.
    """

    def resolve(
        self,
        text: str,
        capabilities: tuple[str, ...],
        catalog: Mapping[str, CapabilitySpec],
    ) -> dict[str, dict[str, object]]:

        parameters: dict[str, dict[str, object]] = {}

        normalized = text.lower()

        for capability_id in capabilities:

            spec = catalog.get(capability_id)

            if spec is None:
                raise ValueError(
                    f"Unknown capability: {capability_id}"
                )

            capability_parameters: dict[str, object] = {}

            if "attributes" in spec.parameter_keys:

                attributes = []

                if "brand" in normalized:
                    attributes.append("brand")

                if "model" in normalized:
                    attributes.append("model")

                if attributes:
                    capability_parameters["attributes"] = attributes

            if capability_parameters:
                parameters[capability_id] = capability_parameters

        return parameters
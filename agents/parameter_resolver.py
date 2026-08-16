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

            for parameter_name, options in (
                spec.parameter_keywords.items()
            ):

                matched_values = []

                for value, keywords in options.items():

                    if any(
                        keyword.lower() in normalized
                        for keyword in keywords
                    ):
                        matched_values.append(value)

                if matched_values:
                    capability_parameters[
                        parameter_name
                    ] = matched_values

            if capability_parameters:
                parameters[capability_id] = capability_parameters

        return parameters
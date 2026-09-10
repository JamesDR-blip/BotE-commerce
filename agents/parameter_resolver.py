from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from domain.capabilities import CapabilitySpec


class ParameterResolver:
    """
    Resolve capability parameters from user intent.

    Optional tenant-scoped memory can override previously corrected
    parameters after validation against the capability contract.
    """

    def __init__(self, memory_service: Any | None = None) -> None:
        self._memory_service = memory_service

    def resolve(
        self,
        text: str,
        capabilities: tuple[str, ...],
        catalog: Mapping[str, CapabilitySpec],
        *,
        workspace_id: str | None = None,
        user_id: str | None = None,
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

        self._apply_memory(
            parameters=parameters,
            capabilities=capabilities,
            catalog=catalog,
            workspace_id=workspace_id,
            user_id=user_id,
        )

        return parameters

    def _apply_memory(
        self,
        *,
        parameters: dict[str, dict[str, object]],
        capabilities: tuple[str, ...],
        catalog: Mapping[str, CapabilitySpec],
        workspace_id: str | None,
        user_id: str | None,
    ) -> None:
        if (
            self._memory_service is None
            or workspace_id is None
            or user_id is None
        ):
            return

        memories = self._memory_service.query(
            workspace_id=workspace_id,
            user_id=user_id,
            memory_type="correction",
        )

        for memory in memories:
            capability_id, separator, parameter_name = memory.key.rpartition(".")

            if (
                not separator
                or capability_id not in capabilities
                or parameter_name not in catalog[capability_id].parameter_keywords
            ):
                continue

            corrected_value = memory.value.get("corrected_value")

            if not isinstance(corrected_value, Mapping):
                continue

            if parameter_name not in corrected_value:
                continue

            proposed_value = corrected_value[parameter_name]

            if not self._is_valid_parameter_value(
                proposed_value,
                catalog[capability_id],
                parameter_name,
            ):
                continue

            parameters.setdefault(capability_id, {})[
                parameter_name
            ] = proposed_value

    @staticmethod
    def _is_valid_parameter_value(
        value: object,
        spec: CapabilitySpec,
        parameter_name: str,
    ) -> bool:
        options = spec.parameter_keywords.get(parameter_name)

        if not options:
            return False

        allowed_values = set(options.keys())

        if isinstance(value, (list, tuple)):
            return bool(value) and all(
                item in allowed_values
                for item in value
            )

        return value in allowed_values

"""Validate execution plans before execution."""

from __future__ import annotations

from typing import Collection, Mapping

from domain.capability_registry import CapabilityRegistry
from domain.plans import ExecutionPlan
from domain.type_contracts import TYPE_CONTRACTS


class PlanValidator:
    """Validate execution plan against capability registry."""

    def validate(
        self,
        plan: ExecutionPlan,
        registry: CapabilityRegistry,
        external_inputs: Collection[str] = (),
    ) -> None:
        available_outputs = set(external_inputs)

        available_output_types: dict[str, type] = {
            key: TYPE_CONTRACTS[key]
            for key in external_inputs
            if key in TYPE_CONTRACTS
        }
        output_owners: dict[str, str] = {
            key: "<external>"
            for key in external_inputs
        }

        for step in plan.steps:
            capability = registry.get(step.capability_id)
            spec = capability.spec

            # ---------------------------------------------------------
            # 1. Capability version
            # ---------------------------------------------------------
            if spec.version != step.capability_version:
                raise ValueError(
                    f"Capability version mismatch for "
                    f"{step.capability_id}: "
                    f"plan requires {step.capability_version}, "
                    f"registered capability is {spec.version}"
                )

            # ---------------------------------------------------------
            # 2. Parameters
            # ---------------------------------------------------------
            unknown_parameters = [
                key
                for key in step.parameters
                if key not in spec.parameter_keys
            ]

            if unknown_parameters:
                raise ValueError(
                    f"Unknown parameter for "
                    f"{step.capability_id}: "
                    f"{', '.join(unknown_parameters)}"
                )

            # ---------------------------------------------------------
            # 3. Input mappings
            # ---------------------------------------------------------
            unknown_mappings = [
                key
                for key in step.input_mapping
                if key not in spec.input_keys
            ]

            if unknown_mappings:
                raise ValueError(
                    f"Unknown input mapping for "
                    f"{step.capability_id}: "
                    f"{', '.join(unknown_mappings)}"
                )

            mapped_input_keys = set(step.input_mapping)

            # ---------------------------------------------------------
            # 4. Required inputs must exist
            # ---------------------------------------------------------
            for input_key in spec.input_keys:
                if input_key in mapped_input_keys:
                    continue

                if input_key in available_outputs:
                    continue

                raise ValueError(
                    f"Missing required input for "
                    f"{step.capability_id}: "
                    f"{input_key}"
                )

            # ---------------------------------------------------------
            # 5. Mapping sources must exist
            # ---------------------------------------------------------
            unknown_sources = [
                source
                for source in step.input_mapping.values()
                if source not in available_outputs
            ]

            if unknown_sources:
                raise ValueError(
                    f"Unknown input mapping source for "
                    f"{step.capability_id}: "
                    f"{', '.join(unknown_sources)}"
                )

            # ---------------------------------------------------------
            # 6. Validate input types
            # ---------------------------------------------------------
            self._validate_unmapped_input_types(
                spec=spec,
                available_output_types=available_output_types,
                mapped_input_keys=mapped_input_keys,
                capability_id=step.capability_id,
            )

            for input_key, source_key in step.input_mapping.items():
                self._validate_mapping_types(
                    source_key=source_key,
                    target_key=input_key,
                    source_types=available_output_types,
                    target_types=spec.input_types,
                    capability_id=step.capability_id,
                )

            # ---------------------------------------------------------
            # 7. Validate outputs / replacements
            # ---------------------------------------------------------
            replacement_outputs = {
                output
                for output in spec.output_keys
                if (
                    output in spec.input_keys
                    and output in spec.input_types
                )
            }

            for output in spec.output_keys:
                if output not in available_outputs:
                    # First producer of this output.
                    continue

                previous_owner = output_owners.get(output)

                # -----------------------------------------------------
                # Case A:
                # The key is still owned by external input.
                #
                # A capability may consume and reproduce an external
                # input under the same key.
                # -----------------------------------------------------
                if previous_owner == "<external>":
                    if output in spec.input_keys:
                        # If a typed input contract exists, validate it.
                        if output in spec.input_types:
                            expected_input_type = spec.input_types[output]
                            previous_type = available_output_types.get(output)

                            if (
                                previous_type is not None
                                and not issubclass(
                                    previous_type,
                                    expected_input_type,
                                )
                            ):
                                raise TypeError(
                                    f"Incompatible input type for "
                                    f"{step.capability_id}: "
                                    f"{output} expects "
                                    f"{expected_input_type.__name__}, "
                                    f"but previous output "
                                    f"{output} provides "
                                    f"{previous_type.__name__}"
                                )

                        continue

                    raise ValueError(
                        f"Output collision for "
                        f"{step.capability_id}: "
                        f"{output}"
                    )

                # -----------------------------------------------------
                # Case B:
                # The key was already produced by another capability.
                #
                # Reproduction is allowed only when the current
                # capability explicitly declares a typed input contract.
                # -----------------------------------------------------
                if output in replacement_outputs:
                    expected_input_type = spec.input_types[output]
                    previous_type = available_output_types.get(output)

                    if (
                        previous_type is not None
                        and not issubclass(
                            previous_type,
                            expected_input_type,
                        )
                    ):
                        raise TypeError(
                            f"Incompatible input type for "
                            f"{step.capability_id}: "
                            f"{output} expects "
                            f"{expected_input_type.__name__}, "
                            f"but previous output "
                            f"{output} provides "
                            f"{previous_type.__name__}"
                        )

                    continue

                # -----------------------------------------------------
                # Case C:
                # Existing output without an explicit typed replacement
                # is a collision.
                # -----------------------------------------------------
                raise ValueError(
                    f"Output collision for "
                    f"{step.capability_id}: "
                    f"{output}"
                )

            # ---------------------------------------------------------
            # 8. Register outputs produced by this step
            # ---------------------------------------------------------
            available_outputs.update(spec.output_keys)

            for output in spec.output_keys:
                output_owners[output] = step.capability_id

                if output in spec.output_types:
                    available_output_types[output] = spec.output_types[output]

    def _validate_unmapped_input_types(
        self,
        spec,
        available_output_types: Mapping[str, type],
        mapped_input_keys: set[str],
        capability_id: str,
    ) -> None:
        """Validate inputs resolved by matching key names."""

        for input_key in spec.input_keys:
            if input_key in mapped_input_keys:
                continue

            if input_key not in available_output_types:
                continue

            if input_key not in spec.input_types:
                continue

            provided_type = available_output_types[input_key]
            expected_type = spec.input_types[input_key]

            if not issubclass(
                provided_type,
                expected_type,
            ):
                raise TypeError(
                    f"Incompatible input type for "
                    f"{capability_id}: "
                    f"{input_key} expects "
                    f"{expected_type.__name__}, "
                    f"but previous output "
                    f"{input_key} provides "
                    f"{provided_type.__name__}"
                )

    def _validate_mapping_types(
        self,
        source_key: str,
        target_key: str,
        source_types: Mapping[str, type],
        target_types: Mapping[str, type],
        capability_id: str,
    ) -> None:
        """Validate the type contract of an explicit input mapping."""

        if (
            source_key not in source_types
            or target_key not in target_types
        ):
            return

        source_type = source_types[source_key]
        target_type = target_types[target_key]

        if not issubclass(
            source_type,
            target_type,
        ):
            raise TypeError(
                f"Incompatible input type for "
                f"{capability_id}: "
                f"{target_key} expects "
                f"{target_type.__name__}, "
                f"but mapped source "
                f"{source_key} provides "
                f"{source_type.__name__}"
            )


__all__ = [
    "PlanValidator",
]
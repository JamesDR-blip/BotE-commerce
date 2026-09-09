from __future__ import annotations

import pytest
import pandas as pd


from domain.capability_registry import CapabilityRegistry
from domain.plans import ExecutionPlan, PlanStep
from execution.planning.plan_validator import PlanValidator

class TypedEchoCapability:
    @property
    def spec(self):
        from domain.capabilities import CapabilitySpec

        return CapabilitySpec(
            id="test.typed_echo",
            version="1.0",
            description="typed echo",
            input_keys=("value",),
            output_keys=("result",),
        )

    def execute(self, context):
        from domain.capabilities import CapabilityResult

        return CapabilityResult(
            outputs={
                "result": context.inputs["value"]
            }
        )

def test_plan_validator_accepts_matching_version():
    registry = CapabilityRegistry()

    registry.register(
        TypedEchoCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.typed_echo",
                capability_version="1.0",
            ),
        )
    )

    PlanValidator().validate(
        plan,
        registry,
        external_inputs={"value"},
    )

def test_plan_validator_rejects_version_mismatch():
    registry = CapabilityRegistry()

    registry.register(
        TypedEchoCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.typed_echo",
                capability_version="2.0",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="version mismatch",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"external_frame"},
        )


def test_plan_validator_rejects_unknown_parameter():
    registry = CapabilityRegistry()

    registry.register(
        TypedEchoCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.typed_echo",
                capability_version="1.0",
                parameters={
                    "unknown": "value",
                },
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)unknown parameter",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"external_frame"},
        )


def test_plan_validator_rejects_unknown_input_mapping():
    registry = CapabilityRegistry()

    registry.register(
        TypedEchoCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.typed_echo",
                capability_version="1.0",
                input_mapping={
                    "unknown": "value",
                },
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)unknown input mapping",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"external_frame"},
        )


class CleanCapability:
    @property
    def spec(self):
        from domain.capabilities import CapabilitySpec

        return CapabilitySpec(
            id="test.clean",
            version="1.0",
            description="clean",
            input_keys=("frame",),
            output_keys=("cleaned_frame",),
        )

    def execute(self, context):
        from domain.capabilities import CapabilityResult

        return CapabilityResult(
            outputs={
                "cleaned_frame": context.inputs["frame"]
            }
        )


class ExtractCapability:
    @property
    def spec(self):
        from domain.capabilities import CapabilitySpec

        return CapabilitySpec(
            id="test.extract",
            version="1.0",
            description="extract",
            input_keys=("cleaned_frame",),
            output_keys=("extracted",),
        )

    def execute(self, context):
        from domain.capabilities import CapabilityResult

        return CapabilityResult(
            outputs={
                "extracted": context.inputs["cleaned_frame"]
            }
        )


def test_plan_validator_accepts_mapping_from_previous_step_output():
    registry = CapabilityRegistry()

    registry.register(CleanCapability())
    registry.register(ExtractCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.clean",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.extract",
                capability_version="1.0",
                input_mapping={
                    "cleaned_frame": "cleaned_frame",
                },
            ),
        )
    )

    PlanValidator().validate(
        plan,
        registry,
        external_inputs={"frame"},
    )


def test_plan_validator_rejects_mapping_from_unknown_source():
    registry = CapabilityRegistry()

    registry.register(ExtractCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.extract",
                capability_version="1.0",
                input_mapping={
                    "cleaned_frame": "does_not_exist",
                },
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)unknown input mapping source",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"external_frame"},
        )


def test_plan_validator_rejects_mapping_from_later_step():
    registry = CapabilityRegistry()

    registry.register(CleanCapability())
    registry.register(ExtractCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.extract",
                capability_version="1.0",
                input_mapping={
                    "cleaned_frame": "cleaned_frame",
                },
            ),
            PlanStep(
                capability_id="test.clean",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)unknown input mapping source",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"external_frame"},
        )


def test_plan_validator_accepts_external_input_mapping():
    registry = CapabilityRegistry()

    registry.register(ExtractCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.extract",
                capability_version="1.0",
                input_mapping={
                    "cleaned_frame": "external_frame",
                },
            ),
        )
    )

    PlanValidator().validate(
        plan,
        registry,
        external_inputs={"external_frame"},
    )


def test_plan_validator_rejects_required_input_without_mapping_or_external_input():
    registry = CapabilityRegistry()

    registry.register(
        TypedEchoCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.typed_echo",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)missing required input",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs=set(),
        )


def test_plan_validator_accepts_unmapped_input_when_external_input_exists():
    registry = CapabilityRegistry()

    registry.register(
        TypedEchoCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.typed_echo",
                capability_version="1.0",
            ),
        )
    )

    PlanValidator().validate(
        plan,
        registry,
        external_inputs={"value"},
    )


def test_plan_validator_accepts_mapped_input_from_previous_output():
    registry = CapabilityRegistry()

    registry.register(CleanCapability())
    registry.register(ExtractCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.clean",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.extract",
                capability_version="1.0",
                input_mapping={
                    "cleaned_frame": "cleaned_frame",
                },
            ),
        )
    )

    PlanValidator().validate(
        plan,
        registry,
        external_inputs={"frame"},
    )


def test_plan_validator_rejects_mapping_from_current_step_output():
    registry = CapabilityRegistry()

    registry.register(
        CleanCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.clean",
                capability_version="1.0",
                input_mapping={
                    "frame": "cleaned_frame",
                },
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)unknown input mapping source",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"frame"},
        )


def test_plan_validator_rejects_output_collision():
    registry = CapabilityRegistry()

    registry.register(
        TypedEchoCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.typed_echo",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.typed_echo",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)output collision",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"value"},
        )


class TypedProducerCapability:
    @property
    def spec(self):
        from domain.capabilities import CapabilitySpec

        return CapabilitySpec(
            id="test.typed_producer",
            version="1.0",
            description="typed producer",
            input_keys=("value",),
            output_keys=("cleaned_frame",),
            output_types={
                "cleaned_frame": str,
            },
        )

    def execute(self, context):
        from domain.capabilities import CapabilityResult

        return CapabilityResult(
            outputs={
                "cleaned_frame": "invalid-frame",
            }
        )


class TypedConsumerCapability:
    @property
    def spec(self):
        from domain.capabilities import CapabilitySpec

        return CapabilitySpec(
            id="test.typed_consumer",
            version="1.0",
            description="typed consumer",
            input_keys=("frame",),
            output_keys=("result",),
            input_types={
                "frame": pd.DataFrame,
            },
        )

    def execute(self, context):
        from domain.capabilities import CapabilityResult

        return CapabilityResult(
            outputs={
                "result": context.inputs["frame"],
            }
        )

def test_plan_validator_rejects_incompatible_mapping_types():
    registry = CapabilityRegistry()

    registry.register(
        TypedProducerCapability()
    )

    registry.register(
        TypedConsumerCapability()
    )

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.typed_producer",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.typed_consumer",
                capability_version="1.0",
                input_mapping={
                    "frame": "cleaned_frame",
                },
            ),
        )
    )

    with pytest.raises(
        TypeError,
        match=r"(?i)incompatible input type",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"value"},
        )


def test_plan_validator_rejects_output_type_collision():
    registry = CapabilityRegistry()

    class StringOutputCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.string_output",
                version="1.0",
                description="string output",
                input_keys=("value",),
                output_keys=("value",),
                output_types={
                    "value": str,
                },
            )

    class IntOutputCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.int_output",
                version="1.0",
                description="int output",
                input_keys=("value",),
                output_keys=("value",),
                output_types={
                    "value": int,
                },
            )

    registry.register(StringOutputCapability())
    registry.register(IntOutputCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.string_output",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.int_output",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)output collision",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"value"},
        )


def test_plan_validator_rejects_incompatible_external_input_type():
    registry = CapabilityRegistry()

    class DataFrameConsumerCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.dataframe-consumer",
                version="1.0",
                description="DataFrame consumer",
                input_keys=("category",),
                output_keys=("result",),
                input_types={
                    "category": pd.DataFrame,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "result": context.inputs["category"],
                }
            )

    registry.register(DataFrameConsumerCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.dataframe-consumer",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        TypeError,
        match=r"(?i)incompatible input type",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"category"},
        )

def test_plan_validator_uses_previous_output_type_over_external_contract():
    registry = CapabilityRegistry()

    class IntProducerCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.int-producer",
                version="1.0",
                description="Produces int under an external key",
                input_keys=("value",),
                output_keys=("value",),
                input_types={
                    "value": str,
                },
                output_types={
                    "value": int,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "value": 123,
                }
            )

    class IntConsumerCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.int-consumer",
                version="1.0",
                description="Consumes int",
                input_keys=("value",),
                output_keys=("result",),
                input_types={
                    "value": int,
                },
                output_types={
                    "result": int,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "result": context.inputs["value"],
                }
            )

    registry.register(IntProducerCapability())
    registry.register(IntConsumerCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.int-producer",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.int-consumer",
                capability_version="1.0",
            ),
        )
    )

    PlanValidator().validate(
        plan,
        registry,
        external_inputs={"value"},
    )


def test_plan_validator_rejects_previous_output_type_against_consumer():
    registry = CapabilityRegistry()

    class IntProducerCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.int-producer",
                version="1.0",
                description="Produces an int under an external key",
                input_keys=("value",),
                output_keys=("value",),
                input_types={
                    "value": str,
                },
                output_types={
                    "value": int,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "value": 123,
                }
            )

    class StringConsumerCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.string-consumer",
                version="1.0",
                description="Consumes str",
                input_keys=("value",),
                output_keys=("result",),
                input_types={
                    "value": str,
                },
                output_types={
                    "result": str,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "result": context.inputs["value"],
                }
            )

    registry.register(IntProducerCapability())
    registry.register(StringConsumerCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.int-producer",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.string-consumer",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        TypeError,
        match=r"(?i)incompatible input type",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"value"},
        )


def test_plan_validator_propagates_output_types_across_multiple_steps():
    registry = CapabilityRegistry()

    class NormalizeCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.normalize",
                version="1.0",
                description="Produces normalized int",
                input_keys=("value",),
                output_keys=("normalized",),
                input_types={
                    "value": str,
                },
                output_types={
                    "normalized": int,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "normalized": 123,
                }
            )

    class ValidateCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.validate",
                version="1.0",
                description="Consumes normalized int",
                input_keys=("normalized",),
                output_keys=("validated",),
                input_types={
                    "normalized": int,
                },
                output_types={
                    "validated": int,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "validated": context.inputs["normalized"],
                }
            )

    class ResultCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.result",
                version="1.0",
                description="Consumes validated int",
                input_keys=("validated",),
                output_keys=("result",),
                input_types={
                    "validated": int,
                },
                output_types={
                    "result": int,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "result": context.inputs["validated"],
                }
            )

    registry.register(NormalizeCapability())
    registry.register(ValidateCapability())
    registry.register(ResultCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.normalize",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.validate",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.result",
                capability_version="1.0",
            ),
        )
    )

    PlanValidator().validate(
        plan,
        registry,
        external_inputs={"value"},
    )


def test_plan_validator_rejects_incompatible_type_after_multiple_steps():
    registry = CapabilityRegistry()

    class NormalizeCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.normalize",
                version="1.0",
                description="Produces normalized int",
                input_keys=("value",),
                output_keys=("normalized",),
                input_types={
                    "value": str,
                },
                output_types={
                    "normalized": int,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "normalized": 123,
                }
            )

    class StringConsumerCapability:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.string-consumer",
                version="1.0",
                description="Incorrectly expects string",
                input_keys=("normalized",),
                output_keys=("result",),
                input_types={
                    "normalized": str,
                },
                output_types={
                    "result": str,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "result": context.inputs["normalized"],
                }
            )

    registry.register(NormalizeCapability())
    registry.register(StringConsumerCapability())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.normalize",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.string-consumer",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        TypeError,
        match=r"(?i)incompatible input type",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"value"},
        )

def test_plan_validator_rejects_output_collision_between_capabilities():
    registry = CapabilityRegistry()

    class FirstProducer:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.first-producer",
                version="1.0",
                description="Produces result",
                input_keys=(),
                output_keys=("result",),
                output_types={
                    "result": int,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={"result": 1}
            )

    class SecondProducer:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.second-producer",
                version="1.0",
                description="Also produces result",
                input_keys=(),
                output_keys=("result",),
                output_types={
                    "result": int,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={"result": 2}
            )

    registry.register(FirstProducer())
    registry.register(SecondProducer())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.first-producer",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.second-producer",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)output collision",
    ):
        PlanValidator().validate(
            plan,
            registry,
        )

def test_plan_validator_allows_capability_to_consume_and_reproduce_same_key():
    registry = CapabilityRegistry()

    class Producer:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.producer",
                version="1.0",
                description="Produces value",
                input_keys=(),
                output_keys=("value",),
                output_types={
                    "value": int,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={"value": 1}
            )

    class Transformer:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.transformer",
                version="1.0",
                description="Consumes and reproduces value",
                input_keys=("value",),
                output_keys=("value",),
                input_types={
                    "value": int,
                },
                output_types={
                    "value": int,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "value": context.inputs["value"] + 1,
                }
            )

    registry.register(Producer())
    registry.register(Transformer())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.producer",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.transformer",
                capability_version="1.0",
            ),
        )
    )

    PlanValidator().validate(
        plan,
        registry,
    )

def test_plan_validator_rejects_output_collision_with_external_input():
    registry = CapabilityRegistry()

    class Producer:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.external-collision",
                version="1.0",
                description="Produces value without consuming it",
                input_keys=(),
                output_keys=("value",),
                output_types={
                    "value": str,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "value": "produced",
                }
            )

    registry.register(Producer())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.external-collision",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=r"(?i)output collision",
    ):
        PlanValidator().validate(
            plan,
            registry,
            external_inputs={"value"},
        )


def test_plan_validator_rejects_incompatible_replacement_after_consume():
    registry = CapabilityRegistry()

    class Producer:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.producer",
                version="1.0",
                description="Produces int",
                input_keys=(),
                output_keys=("value",),
                output_types={
                    "value": int,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "value": 1,
                }
            )

    class StringTransformer:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.string-transformer",
                version="1.0",
                description="Consumes int but produces str",
                input_keys=("value",),
                output_keys=("value",),
                input_types={
                    "value": int,
                },
                output_types={
                    "value": str,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "value": str(context.inputs["value"]),
                }
            )

    class IntConsumer:
        @property
        def spec(self):
            from domain.capabilities import CapabilitySpec

            return CapabilitySpec(
                id="test.int-consumer",
                version="1.0",
                description="Consumes int",
                input_keys=("value",),
                output_keys=("result",),
                input_types={
                    "value": int,
                },
                output_types={
                    "result": int,
                },
            )

        def execute(self, context):
            from domain.capabilities import CapabilityResult

            return CapabilityResult(
                outputs={
                    "result": context.inputs["value"],
                }
            )

    registry.register(Producer())
    registry.register(StringTransformer())
    registry.register(IntConsumer())

    plan = ExecutionPlan(
        steps=(
            PlanStep(
                capability_id="test.producer",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.string-transformer",
                capability_version="1.0",
            ),
            PlanStep(
                capability_id="test.int-consumer",
                capability_version="1.0",
            ),
        )
    )

    with pytest.raises(
        TypeError,
        match=r"(?i)incompatible input type",
    ):
        PlanValidator().validate(
            plan,
            registry,
        )

from domain.capabilities import CapabilitySpec


def make_spec(
    capability_id: str,
    required_capabilities: tuple[str, ...] = (),
) -> CapabilitySpec:
    return CapabilitySpec(
        id=capability_id,
        version="1.0",
        description=f"{capability_id} capability",
        input_keys=(),
        output_keys=(),
        required_capabilities=required_capabilities,
    )

def test_capability_without_dependencies_is_kept():
    spec = make_spec("data.clean")

    assert spec.required_capabilities == ()
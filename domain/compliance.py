from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class CompliancePolicy:
    id: str
    organization_id: str
    name: str
    resource: str
    action: str
    condition: Mapping[str, str]
    reason: str
    enabled: bool = True

    def __post_init__(self) -> None:
        for field_name, value in (
            ("id", self.id),
            ("organization_id", self.organization_id),
            ("name", self.name),
            ("resource", self.resource),
            ("action", self.action),
            ("reason", self.reason),
        ):
            if not value or not value.strip():
                raise ValueError(f"{field_name} must not be blank")

        normalized = {}
        for key, value in self.condition.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("condition keys must not be blank")
            if not isinstance(value, str):
                raise ValueError("condition values must be strings")
            normalized[key] = value

        object.__setattr__(
            self,
            "condition",
            MappingProxyType(normalized),
        )

    def matches(
        self,
        *,
        resource: str,
        action: str,
        context: Mapping[str, str],
    ) -> bool:
        if not self.enabled:
            return False

        if self.resource != resource or self.action != action:
            return False

        return all(context.get(key) == value for key, value in self.condition.items())


@dataclass(frozen=True)
class ComplianceDecision:
    allowed: bool
    reason: str

    @classmethod
    def allow(cls, reason: str = "No applicable compliance policy") -> "ComplianceDecision":
        return cls(allowed=True, reason=reason)

    @classmethod
    def deny(cls, reason: str) -> "ComplianceDecision":
        if not reason or not reason.strip():
            raise ValueError("deny reason must not be blank")
        return cls(allowed=False, reason=reason)

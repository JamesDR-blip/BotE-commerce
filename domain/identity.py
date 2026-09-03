from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    roles: frozenset[str] = frozenset()
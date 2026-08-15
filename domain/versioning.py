"""Capability version constraint helpers."""

from __future__ import annotations


def satisfies(
    version: str,
    constraint: str,
) -> bool:
    """
    Check whether a capability version satisfies
    a dependency constraint.
    """

    if not constraint:
        return True

    if constraint.startswith(">="):
        required = constraint[2:]
        return version >= required

    if constraint.startswith("=="):
        required = constraint[2:]
        return version == required

    return version == constraint
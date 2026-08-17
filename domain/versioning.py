"""Capability version constraint helpers."""

from __future__ import annotations

from packaging.specifiers import SpecifierSet
from packaging.version import Version


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

    return Version(version) in SpecifierSet(constraint)
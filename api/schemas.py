"""Backward-compatible imports for HTTP response contracts.

HTTP schemas now live in :mod:`schemas.responses`.
"""
from schemas.responses import ValidationResponse

__all__ = ["ValidationResponse"]

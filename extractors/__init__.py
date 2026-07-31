"""Product-attribute extractor contracts and built-in implementations."""

from .base import ExtractedAttributes, ProductExtractor
from .deterministic import DeterministicProductExtractor

__all__ = ["DeterministicProductExtractor", "ExtractedAttributes", "ProductExtractor"]

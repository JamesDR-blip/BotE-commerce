# SPRINT 08: Product Attribute Extraction

## Status
Completed

## Objective
Provide deterministic extraction of key e-commerce catalog attributes from unstructured product titles.

## Deliverables
- extractors/base.py: Extractor interface (ProductExtractor).
- extractors/deterministic.py: Regex and vocabulary-based extraction for brand, model, color, size, weight, material, voltage, capacity, SKU, UPC, GTIN.
- gents/extraction.py: ExtractionAgent integrating extraction into pipeline.

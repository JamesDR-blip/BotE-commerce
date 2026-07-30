"""Home appliances category validator plugin."""
from __future__ import annotations
import pandas as pd
from domain.models import ValidationIssue
from services.duplicate_detection import DuplicateDetection
from services.format_validation import FormatValidation
from services.missing_value_validation import MissingValueValidation
from services.title_extraction import extract_product_attributes
from validators.base import CategoryValidator


class HomeAppliancesValidator(CategoryValidator):
    category = "HomeAppliances"
    def autofix(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Enrich titles and build a canonical title used for deduplication."""
        result = frame.copy()
        title_column = next((column for column in result.columns if str(column).casefold() == "product_title"), None)
        if title_column is None:
            return result
        extracted = result[title_column].map(extract_product_attributes)
        result["Brands"] = extracted.map(lambda item: item.brand)
        result["Model_Series"] = extracted.map(lambda item: item.model_series)
        result["Products"] = extracted.map(lambda item: item.products)
        result["Material"] = extracted.map(lambda item: item.material)
        result["Spec"] = extracted.map(lambda item: item.spec)
        result["Attribute_Special"] = extracted.map(lambda item: item.attribute_special)
        result["standard_title"] = extracted.map(lambda item: item.standard_title())
        # Keep a readable fallback for products outside the controlled vocabulary.
        result["standard_title"] = result["standard_title"].mask(result["standard_title"].eq(""), result[title_column].fillna("").astype(str).str.strip())
        return result
    def validate(self, frame: pd.DataFrame, rules: dict) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        names = {str(c).casefold(): c for c in frame.columns}
        duplicates = DuplicateDetection(); formats = FormatValidation(); missing_values = MissingValueValidation()
        # Product feeds can be title-only. Enrichment is still useful without
        # technical Power/Dimensions columns, so those fields are optional.
        if "power" in names:
            issues.extend(formats.contains_regex(frame[names["power"]], r"\b\d+(?:[.,]\d+)?\s*k?W\b", "Power", "invalid_power", "Power needs W or kW"))
        if "dimensions" in names:
            pattern = r"^\s*\d+(?:[.,]\d+)?\s*[x×]\s*\d+(?:[.,]\d+)?\s*[x×]\s*\d+(?:[.,]\d+)?\s*(?:cm)?\s*$"
            issues.extend(formats.matches_regex(frame[names["dimensions"]], pattern, "Dimensions", "invalid_dimensions", "Dimensions need D x R x C (cm)"))
        if "product_title" not in names:
            issues.extend(missing_values.missing_column(frame, "product_title", "missing_title", "product_title is required for enrichment", use_frame_index=True))
        else:
            # A canonical title intentionally omits unrecognised marketing
            # details; using it as a dedupe key can therefore merge distinct
            # SKUs. Deduplicate only equivalent source titles.
            issues.extend(duplicates.normalized_text_duplicates(frame[names["product_title"]], "product_title", "duplicate_product", "Duplicate normalized product title"))
        return issues

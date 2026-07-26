"""Home appliances category validator plugin."""
from __future__ import annotations
import pandas as pd
from models.domain import ValidationIssue
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
        # Product feeds can be title-only. Enrichment is still useful without
        # technical Power/Dimensions columns, so those fields are optional.
        if "power" in names:
            vals = frame[names["power"]].fillna("").astype(str)
            issues.extend(ValidationIssue(i + 2, "Power", "invalid_power", "Power needs W or kW") for i in vals.index[~vals.str.contains(r"\b\d+(?:[.,]\d+)?\s*k?W\b", case=False, regex=True)])
        if "dimensions" in names:
            vals = frame[names["dimensions"]].fillna("").astype(str)
            pattern = r"^\s*\d+(?:[.,]\d+)?\s*[x×]\s*\d+(?:[.,]\d+)?\s*[x×]\s*\d+(?:[.,]\d+)?\s*(?:cm)?\s*$"
            issues.extend(ValidationIssue(i + 2, "Dimensions", "invalid_dimensions", "Dimensions need D x R x C (cm)") for i in vals.index[~vals.str.match(pattern, case=False)])
        if "product_title" not in names:
            issues.extend(ValidationIssue(i + 2, "product_title", "missing_title", "product_title is required for enrichment") for i in frame.index)
        else:
            # A canonical title intentionally omits unrecognised marketing
            # details; using it as a dedupe key can therefore merge distinct
            # SKUs. Deduplicate only equivalent source titles.
            normalized_titles = frame[names["product_title"]].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().str.casefold()
            duplicates = normalized_titles.duplicated(keep="first")
            issues.extend(ValidationIssue(i + 2, "product_title", "duplicate_product", "Duplicate normalized product title") for i in frame.index[duplicates])
        return issues

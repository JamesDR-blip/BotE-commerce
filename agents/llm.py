"""Optional, text-only LLM assistant. It never returns executable instructions."""
from __future__ import annotations
from models.domain import ValidationIssue


class LLMAssistantAgent:
    def __init__(self, enabled: bool, api_key: str | None, model: str) -> None:
        self._enabled, self._api_key, self._model = enabled, api_key, model
    def _ask(self, task: str, issues: list[ValidationIssue]) -> str:
        if not self._enabled: return "LLM mode is disabled."
        if not self._api_key: return "LLM mode is enabled but GOOGLE_API_KEY is not configured."
        from google import genai
        client = genai.Client(api_key=self._api_key)
        evidence = "\n".join(f"row {x.row}, {x.field}: {x.message}" for x in issues[:50])
        response = client.models.generate_content(model=self._model, contents=f"{task}\nValidation evidence:\n{evidence}\nReturn concise plain text. Never provide executable code.")
        return response.text or "No explanation returned."
    def explain_errors(self, issues: list[ValidationIssue]) -> str: return self._ask("Explain these data quality errors for a business user.", issues)
    def suggest_fixes(self, issues: list[ValidationIssue]) -> str: return self._ask("Suggest safe, manual data corrections for these errors.", issues)
    def summarize_report(self, issues: list[ValidationIssue]) -> str: return self._ask("Summarize the quality report and its top risks.", issues)

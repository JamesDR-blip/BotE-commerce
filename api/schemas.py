"""API contracts."""
from pydantic import BaseModel

class ValidationResponse(BaseModel):
    execution_id: str
    category: str
    health_score: float
    reports: dict[str, str]
    cached: bool

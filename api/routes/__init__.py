"""API route aggregation."""

from api.routes.data import router as data_router
from api.routes.datasets import router as datasets_router
from api.routes.executions import router as executions_router
from api.routes.health import router as health_router
from api.routes.rules import router as rules_router
from api.routes.studio import router as studio_router
from api.routes.workflows import router as workflows_router
from api.routes.risk import router as risk_router
from api.routes.approval import router as approval_router
from .system import router as system_router

__all__ = [
    "data_router",
    "datasets_router",
    "executions_router",
    "health_router",
    "rules_router",
    "studio_router",
    "workflows_router",
    "risk_router",
    "approval_router",
    "system_router",
]

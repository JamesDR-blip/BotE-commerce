"""API route aggregation."""

from api.routes.data import router as data_router
from api.routes.datasets import router as datasets_router
from api.routes.executions import router as executions_router
from api.routes.studio import router as studio_router
from api.routes.workflows import router as workflows_router
from .system import router as system_router

__all__ = [
    "data_router",
    "datasets_router",
    "executions_router",
    "studio_router",
    "workflows_router",
    "system_router",
]
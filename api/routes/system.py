"""System API routes."""

from fastapi import APIRouter, Depends

from api.dependencies import get_categories

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/categories")
def categories(
    values: list[str] = Depends(get_categories),
) -> dict[str, list[str]]:
    return {"categories": values}
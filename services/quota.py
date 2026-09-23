"""Organization quota enforcement service."""

from __future__ import annotations

from repositories.quotas import QuotaRepository
from domain.exceptions import QuotaExceededError
from domain.quota import QuotaDimension


class QuotaService:
    """Evaluates hard organization quotas before governed mutations."""

    def __init__(
        self,
        *,
        quotas: QuotaRepository,
    ) -> None:
        self.quotas = quotas

    def check(
        self,
        *,
        organization_id: str | None,
        dimension: QuotaDimension,
        requested_usage: int,
    ) -> None:
        if organization_id is None:
            return

        if requested_usage < 0:
            raise ValueError("requested_usage must be non-negative")

        quota = self.quotas.get_quota(
            organization_id=organization_id,
            dimension=dimension,
        )

        # No configured quota means unlimited for this dimension.
        if quota is None:
            return

        current_usage = self.quotas.get_usage(
            organization_id=organization_id,
            dimension=dimension,
        )

        projected_usage = current_usage + requested_usage

        if projected_usage > quota.limit:
            raise QuotaExceededError(
                dimension=dimension.value,
                current_usage=current_usage,
                requested_usage=requested_usage,
                limit=quota.limit,
            )

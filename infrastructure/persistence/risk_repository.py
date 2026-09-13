from typing import Callable
from sqlalchemy.orm import Session

from database.models import RiskPolicyRecord
from domain.risk import RiskPolicy

class RiskRepository:
    """SQLAlchemy repository for persisting and retrieving risk policy configuration."""

    def __init__(self, sessions: Callable[[], Session]):
        self._sessions = sessions

    def get_policy(self) -> RiskPolicy:
        """Return the currently configured :class:`RiskPolicy`.

        The ``risk_policies`` table is expected to contain a single row with
        ``high_risk_threshold`` and ``critical_risk_threshold`` columns.
        If no row exists we fall back to the default ``RiskPolicy`` values.
        """
        with self._sessions() as session:
            record = session.query(RiskPolicyRecord).first()
            if record is None:
                return RiskPolicy()
            return RiskPolicy(
                high_risk_threshold=record.high_risk_threshold,
                critical_risk_threshold=record.critical_risk_threshold,
            )

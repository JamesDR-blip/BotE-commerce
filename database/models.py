"""SQLAlchemy persistence schema."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class ExecutionRecord(Base):
    __tablename__ = "executions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    source_hash: Mapped[str] = mapped_column(String(64), index=True)
    rule_version: Mapped[str] = mapped_column(String(64))
    health_score: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    reports: Mapped[list["ReportRecord"]] = relationship(back_populates="execution", cascade="all, delete-orphan")
    logs: Mapped[list["ValidationLogRecord"]] = relationship(back_populates="execution", cascade="all, delete-orphan")


class ValidationLogRecord(Base):
    __tablename__ = "validation_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[str] = mapped_column(ForeignKey("executions.id"), index=True)
    row_number: Mapped[int] = mapped_column(Integer)
    field: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    execution: Mapped[ExecutionRecord] = relationship(back_populates="logs")


class ReportRecord(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[str] = mapped_column(ForeignKey("executions.id"), index=True)
    format: Mapped[str] = mapped_column(String(12))
    path: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    execution: Mapped[ExecutionRecord] = relationship(back_populates="reports")


def make_session_factory(url: str) -> sessionmaker[Session]:
    engine = create_engine(url, future=True, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)

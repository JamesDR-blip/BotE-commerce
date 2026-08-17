"""SQLAlchemy persistence schema."""
from __future__ import annotations

import uuid

from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship, 
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

class Base(DeclarativeBase):
    pass


class UserRecord(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    executions: Mapped[list["ExecutionRecord"]] = relationship(back_populates="user")


class ExecutionRecord(Base):
    __tablename__ = "executions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    source_hash: Mapped[str] = mapped_column(String(64), index=True)
    rule_version: Mapped[str] = mapped_column(String(64))
    health_score: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(
        String(20),
        default="COMPLETED", 
        nullable=False,
        )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        index=True,
    )

    requirement_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    plan_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    planner_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    user: Mapped[UserRecord | None] = relationship(
        back_populates="executions"
        )
    reports: Mapped[list["ReportRecord"]] = relationship(
        back_populates="execution",
        cascade="all, delete-orphan"
    )

    logs: Mapped[list["ValidationLogRecord"]] = relationship(
        back_populates="execution",
        cascade="all, delete-orphan"
    )


    capability_traces = relationship(
        "CapabilityExecutionTraceRecord",
        back_populates="execution",
        cascade="all, delete-orphan",
    )

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

class CapabilityExecutionTraceRecord(Base):
    __tablename__ = "capability_execution_traces"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    execution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("executions.id"),
        nullable=False,
        index=True,
    )

    capability_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    capability_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    inputs_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    outputs_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    duration_ms: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    execution = relationship(
        "ExecutionRecord",
        back_populates="capability_traces",
    )

class ReportRecord(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[str] = mapped_column(ForeignKey("executions.id"), index=True)
    format: Mapped[str] = mapped_column(String(12))
    path: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    execution: Mapped[ExecutionRecord] = relationship(back_populates="reports")


def make_session_factory(url: str):
    if url == "sqlite://":
        engine = create_engine(
            url,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(
            url,
            future=True,
            connect_args={"check_same_thread": False}
            if url.startswith("sqlite")
            else {},
        )

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)
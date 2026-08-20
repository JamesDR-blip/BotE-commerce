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

class WorkspaceRecord(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    projects: Mapped[list["ProjectRecord"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )

class ProjectRecord(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


    workspace: Mapped[WorkspaceRecord] = relationship(
        back_populates="projects"
    )

    datasets: Mapped[list["DatasetRecord"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )

    workflows: Mapped[list["WorkflowRecord"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )

class DatasetRecord(Base):

    __tablename__ = "datasets"


    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )


    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )


    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )


    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )


    metadata_json: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


    project: Mapped[ProjectRecord] = relationship(
        back_populates="datasets"
    )

class WorkflowRecord(Base):

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    active_version: Mapped[str] = mapped_column(
        String(50),
        default="1.0",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="DRAFT",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    project: Mapped["ProjectRecord"] = relationship(
        back_populates="workflows"
    )

    versions: Mapped[list["WorkflowVersionRecord"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
    )
    executions: Mapped[list["WorkflowExecutionRecord"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
    )

class WorkflowVersionRecord(Base):

    __tablename__ = "workflow_versions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    workflow_id: Mapped[str] = mapped_column(
        ForeignKey("workflows.id"),
        nullable=False,
        index=True,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    plan_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    workflow: Mapped["WorkflowRecord"] = relationship(
        back_populates="versions"
    )

class WorkflowExecutionRecord(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    workflow_id: Mapped[str] = mapped_column(
        ForeignKey("workflows.id"),
        nullable=False,
        index=True,
    )

    workflow_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
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

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    workflow: Mapped["WorkflowRecord"] = relationship(
        back_populates="executions"
    )

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
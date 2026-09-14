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
    Index,
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
from sqlalchemy import UniqueConstraint

class Base(DeclarativeBase):
    pass


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    executions: Mapped[list["ExecutionRecord"]] = relationship(
        back_populates="user"
    )

    workspaces: Mapped[list["WorkspaceRecord"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
class WorkspaceRecord(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
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

    owner: Mapped[UserRecord] = relationship(
        back_populates="workspaces"
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

    filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    file_format: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    size_bytes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    storage_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    row_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    column_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="READY",
        nullable=False,
        index=True,
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
    
    __table_args__ = (
        UniqueConstraint(
            "workflow_id",
            "version",
            name="uq_workflow_version",
        ),
    )

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

    dataset_id: Mapped[str | None] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=True,
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

    capability_traces: Mapped[list["CapabilityExecutionTraceRecord"]] = relationship(
        back_populates="workflow_execution",
        cascade="all, delete-orphan",
    )

class ExecutionRecord(Base):
    __tablename__ = "executions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    dataset_id: Mapped[str | None] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=True,
        index=True,
    )
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
    execution_traces: Mapped[list["ExecutionTraceRecord"]] = relationship(
        back_populates="execution",
        cascade="all, delete-orphan",
    )


class AgentMemoryRecord(Base):
    __tablename__ = "agent_memory"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    memory_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    memory_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    value_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        Index(
            "ix_agent_memory_scope_type_key",
            "workspace_id",
            "user_id",
            "memory_type",
            "memory_key",
        ),
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

class ExecutionTraceRecord(Base):
    __tablename__ = "execution_traces"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    execution_id: Mapped[str] = mapped_column(
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

    execution: Mapped["ExecutionRecord"] = relationship(
        back_populates="execution_traces",
    )

class CapabilityExecutionTraceRecord(Base):
    __tablename__ = "capability_execution_traces"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    workflow_execution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflow_executions.id"),
        nullable=False,
        index=True,
    )

    @property
    def execution_id(self) -> str:
        return self.workflow_execution_id


    @execution_id.setter
    def execution_id(self, value: str) -> None:
        self.workflow_execution_id = value

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
    workflow_execution = relationship(
        "WorkflowExecutionRecord",
        back_populates="capability_traces",
    )

class ApprovalRecord(Base):
    """Persistence model for approval workflow requests and decisions."""

    __tablename__ = "approvals"

    approval_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    execution_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_executions.id"),
        nullable=False,
        index=True,
    )
    changeset_id: Mapped[str] = mapped_column(
        ForeignKey("changesets.id"),
        nullable=False,
        index=True,
    )
    risk_score: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    decision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relationship back to execution if needed
    execution = relationship(
        "WorkflowExecutionRecord",
        backref="approvals",
        foreign_keys=[execution_id],
    )

class RiskAssessmentRecord(Base):
    """Persistence model for workflow execution risk assessments."""

    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    execution_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_executions.id"),
        nullable=False,
        index=True,
    )

    risk_score: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    approval_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    execution = relationship(
        "WorkflowExecutionRecord",
        backref="risk_assessments",
        foreign_keys=[execution_id],
    )


class ChangeSetRecord(Base):
    __tablename__ = "changesets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=False,
        index=True,
    )

    execution_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_executions.id"),
        nullable=False,
        index=True,
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

    before_storage_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    before_content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    after_storage_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    after_content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    rolled_back_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    items: Mapped[list["ChangeSetItemRecord"]] = relationship(
        back_populates="changeset",
        cascade="all, delete-orphan",
    )


class ChangeSetItemRecord(Base):
    __tablename__ = "changeset_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    changeset_id: Mapped[str] = mapped_column(
        ForeignKey("changesets.id"),
        nullable=False,
        index=True,
    )

    entity: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    record_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    before_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    after_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    changeset: Mapped["ChangeSetRecord"] = relationship(
        back_populates="items",
    )

class DataLineageEventRecord(Base):
    __tablename__ = "data_lineage_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=False,
        index=True,
    )

    execution_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_executions.id"),
        nullable=False,
        index=True,
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

    capability_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    capability_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    input_refs_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    output_refs_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )


class AuditEventRecord(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )

    actor_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    resource_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    execution_id: Mapped[str | None] = mapped_column(
        ForeignKey("workflow_executions.id"),
        nullable=True,
        index=True,
    )

    changeset_id: Mapped[str | None] = mapped_column(
        ForeignKey("changesets.id"),
        nullable=True,
        index=True,
    )

    metadata_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    previous_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    event_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

class RiskPolicyRecord(Base):
    """Persistence model for risk policy thresholds."""
    __tablename__ = "risk_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    high_risk_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    critical_risk_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.9)

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

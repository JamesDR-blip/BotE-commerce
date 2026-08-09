"""SQLAlchemy persistence schema."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    user: Mapped[UserRecord | None] = relationship(back_populates="executions")
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
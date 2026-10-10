"""Read-only validation of database schema against SQLAlchemy metadata."""
from __future__ import annotations

from sqlalchemy import inspect
from sqlalchemy.engine import Connection
from sqlalchemy.schema import MetaData

from database.models import Base


class SchemaDriftError(RuntimeError):
    """Raised when required tables or columns are missing."""


def validate_database_schema(
    connection: Connection,
    *,
    metadata: MetaData | None = None,
) -> None:
    """Raise SchemaDriftError when metadata-required tables or columns are absent.

    This function is read-only: it never creates, alters, or migrates schema.
    Extra tables and differences in types, indexes, or constraints are not
    checked by this initial validator.
    """
    expected_metadata = metadata if metadata is not None else Base.metadata
    inspector = inspect(connection)
    actual_tables = set(inspector.get_table_names())
    expected_tables = set(expected_metadata.tables)

    missing_tables = sorted(expected_tables - actual_tables)
    missing_columns: list[str] = []

    for table_name in sorted(expected_tables & actual_tables):
        actual_columns = {
            column["name"]
            for column in inspector.get_columns(table_name)
        }
        expected_columns = {
            column.name
            for column in expected_metadata.tables[table_name].columns
        }
        missing_columns.extend(
            f"{table_name}.{column_name}"
            for column_name in sorted(expected_columns - actual_columns)
        )

    problems: list[str] = []
    if missing_tables:
        problems.append("missing tables: " + ", ".join(missing_tables))
    if missing_columns:
        problems.append("missing columns: " + ", ".join(missing_columns))

    if problems:
        raise SchemaDriftError(
            "Database schema drift detected: " + "; ".join(problems)
        )

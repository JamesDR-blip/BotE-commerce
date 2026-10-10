from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, inspect

from database.models import Base
from database.schema_validation import (
    SchemaDriftError,
    validate_database_schema,
)


def test_schema_validator_accepts_complete_metadata_schema():
    engine = create_engine("sqlite://")
    try:
        Base.metadata.create_all(engine)
        with engine.connect() as connection:
            validate_database_schema(connection)
    finally:
        engine.dispose()


def test_schema_validator_reports_missing_table_without_creating_it():
    metadata = MetaData()
    Table(
        "required_widget",
        metadata,
        Column("id", Integer, primary_key=True),
    )
    engine = create_engine("sqlite://")
    try:
        with engine.connect() as connection:
            try:
                validate_database_schema(connection, metadata=metadata)
            except SchemaDriftError as exc:
                assert "missing tables: required_widget" in str(exc)
            else:
                raise AssertionError("Missing table was not detected")

            assert "required_widget" not in inspect(connection).get_table_names()
    finally:
        engine.dispose()


def test_schema_validator_reports_missing_column_without_altering_table():
    metadata = MetaData()
    Table(
        "required_widget",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(100), nullable=False),
    )
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE required_widget (id INTEGER PRIMARY KEY)"
            )

        with engine.connect() as connection:
            try:
                validate_database_schema(connection, metadata=metadata)
            except SchemaDriftError as exc:
                assert "missing columns: required_widget.name" in str(exc)
            else:
                raise AssertionError("Missing column was not detected")

            columns = {
                column["name"]
                for column in inspect(connection).get_columns("required_widget")
            }
            assert columns == {"id"}
    finally:
        engine.dispose()

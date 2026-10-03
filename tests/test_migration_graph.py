"""Database-free structural checks for the active Alembic baseline."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from alembic.script import ScriptDirectory

from database.models import Base

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "database" / "migrations"
VERSIONS = MIGRATIONS / "versions"
BASELINE = VERSIONS / "20261002_01_canonical_postgresql_baseline.py"
ARCHIVE = MIGRATIONS / "archive" / "legacy_versions"


def _attribute_call(node: ast.AST, owner: str, attribute: str) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == owner
        and node.func.attr == attribute
    )


def _type_signature(node: ast.Call) -> tuple[str, int | None, bool | None]:
    assert isinstance(node.func, ast.Attribute)
    name = node.func.attr
    keywords = {item.arg: item.value for item in node.keywords}
    length_node = keywords.get("length")
    if length_node is None and node.args and isinstance(node.args[0], ast.Constant):
        length_node = node.args[0]
    length = length_node.value if isinstance(length_node, ast.Constant) else None
    timezone_node = keywords.get("timezone")
    timezone = timezone_node.value if isinstance(timezone_node, ast.Constant) else None
    if name == "DateTime" and timezone is None:
        timezone = False
    return name, length, timezone


def _constraint_columns(node: ast.Call) -> tuple[str, ...]:
    return tuple(
        item.value
        for item in node.args
        if isinstance(item, ast.Constant) and isinstance(item.value, str)
    )


def _baseline_ast() -> ast.Module:
    return ast.parse(BASELINE.read_text(encoding="utf-8"))


def test_active_migration_history_is_one_new_baseline_and_one_head() -> None:
    scripts = ScriptDirectory(str(MIGRATIONS))
    assert scripts.get_heads() == ["20261002_01"]
    assert scripts.get_bases() == ["20261002_01"]
    revisions = list(scripts.walk_revisions())
    assert len(revisions) == 1
    assert revisions[0].down_revision is None

    archived = list(ARCHIVE.glob("*.py"))
    assert len(archived) == 23
    archived_ids = {
        match.group(1)
        for path in archived
        if (match := re.search(
            r"(?m)^revision(?:\s*:\s*[^=]+)?\s*=\s*['\"]([^'\"]+)",
            path.read_text(encoding="utf-8-sig"),
        ))
    }
    assert len(archived_ids) == 23
    assert archived_ids.isdisjoint({revision.revision for revision in revisions})


def test_baseline_matches_orm_table_columns_constraints_and_indexes() -> None:
    tree = _baseline_ast()
    table_ops = {
        call.args[0].value: call
        for call in ast.walk(tree)
        if _attribute_call(call, "op", "create_table")
        and call.args
        and isinstance(call.args[0], ast.Constant)
    }
    assert set(table_ops) == set(Base.metadata.tables)
    assert len(table_ops) == 31
    assert sum(len(table.foreign_keys) for table in Base.metadata.tables.values()) == 43

    for table_name, table in Base.metadata.tables.items():
        operation = table_ops[table_name]
        columns: dict[str, ast.Call] = {}
        for call in ast.walk(operation):
            if not _attribute_call(call, "sa", "Column"):
                continue
            assert isinstance(call.args[0], ast.Constant)
            columns[call.args[0].value] = call

        assert set(columns) == set(table.columns.keys()), table_name
        for column_name, column in table.columns.items():
            column_call = columns[column_name]
            type_call = column_call.args[1]
            assert isinstance(type_call, ast.Call)
            expected_type = type(column.type).__name__
            expected_length = getattr(column.type, "length", None)
            expected_timezone = getattr(column.type, "timezone", None)
            assert _type_signature(type_call) == (
                expected_type,
                expected_length,
                expected_timezone,
            ), f"{table_name}.{column_name}"
            keywords = {item.arg: item.value for item in column_call.keywords}
            assert keywords["nullable"].value is column.nullable
            assert "server_default" not in keywords

        constraints = [
            call
            for call in ast.walk(operation)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.value.id == "sa"
            and call.func.attr
            in {"PrimaryKeyConstraint", "UniqueConstraint", "ForeignKeyConstraint"}
        ]
        actual_primary_key = {
            _constraint_columns(call)
            for call in constraints
            if call.func.attr == "PrimaryKeyConstraint"
        }
        assert actual_primary_key == {
            tuple(column.name for column in table.primary_key.columns)
        }, table_name

        actual_unique = {
            (call.keywords[0].value.value if call.keywords else None, _constraint_columns(call))
            for call in constraints
            if call.func.attr == "UniqueConstraint"
        }
        expected_unique = {
            (constraint.name, tuple(column.name for column in constraint.columns))
            for constraint in table.constraints
            if constraint.__class__.__name__ == "UniqueConstraint"
        }
        assert actual_unique == expected_unique, table_name

        actual_foreign_keys = {
            (
                tuple(item.value for item in call.args[0].elts),
                tuple(item.value for item in call.args[1].elts),
            )
            for call in constraints
            if call.func.attr == "ForeignKeyConstraint"
        }
        expected_foreign_keys = {
            (
                tuple(element.parent.name for element in constraint.elements),
                tuple(element.target_fullname for element in constraint.elements),
            )
            for constraint in table.foreign_key_constraints
        }
        assert actual_foreign_keys == expected_foreign_keys, table_name
        assert all(
            "ondelete" not in {item.arg for item in call.keywords}
            and "onupdate" not in {item.arg for item in call.keywords}
            for call in constraints
            if call.func.attr == "ForeignKeyConstraint"
        ), table_name

    baseline_indexes = {
        (
            call.args[0].args[0].value
            if _attribute_call(call.args[0], "op", "f")
            else call.args[0].value,
            call.args[1].value,
            tuple(item.value for item in call.args[2].elts),
            next(
                (keyword.value.value for keyword in call.keywords if keyword.arg == "unique"),
                False,
            ),
        )
        for call in ast.walk(tree)
        if _attribute_call(call, "op", "create_index")
    }
    expected_indexes = {
        (index.name, table.name, tuple(column.name for column in index.columns), index.unique)
        for table in Base.metadata.tables.values()
        for index in table.indexes
    }
    assert baseline_indexes == expected_indexes
    assert len(baseline_indexes) == 67

    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "create_all"
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.ImportFrom)
        and node.module == "database.models"
        for node in ast.walk(tree)
    )
    assert not any(
        _attribute_call(node, "op", "execute")
        or _attribute_call(node, "op", "bulk_insert")
        for node in ast.walk(tree)
    )
    assert not any(
        _attribute_call(node, "sa", "CheckConstraint")
        or _attribute_call(node, "sa", "Enum")
        for node in ast.walk(tree)
    )

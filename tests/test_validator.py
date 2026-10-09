from pathlib import Path

import pandas as pd
import pytest

from universal_data_normalizer.validator import ColumnRule, SchemaConfig, validate


def _write_schema(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "schema.json"
    path.write_text(content, encoding="utf-8")
    return path


def test_schema_config_from_file(tmp_path: Path) -> None:
    path = _write_schema(
        tmp_path,
        '{"columns": {"name": {"required": true, "dtype": "string", "nullable": false}}}',
    )

    schema = SchemaConfig.from_file(path)

    rule = schema.columns["name"]
    assert rule.required is True
    assert rule.dtype == "string"
    assert rule.nullable is False


def test_schema_config_applies_defaults(tmp_path: Path) -> None:
    path = _write_schema(tmp_path, '{"columns": {"name": {}}}')

    schema = SchemaConfig.from_file(path)

    rule = schema.columns["name"]
    assert rule.required is True
    assert rule.dtype is None
    assert rule.nullable is True


@pytest.mark.parametrize("content", ["[]", "{}", '{"columns": []}'])
def test_schema_config_rejects_invalid_shape(tmp_path: Path, content: str) -> None:
    path = _write_schema(tmp_path, content)

    with pytest.raises(ValueError, match="Invalid schema file"):
        SchemaConfig.from_file(path)


def test_validate_reports_missing_required_column() -> None:
    schema = SchemaConfig(columns={"name": ColumnRule(required=True)})
    df = pd.DataFrame({"age": [24]})

    issues = validate(df, schema)

    assert any("Missing required column 'name'" in issue for issue in issues)


def test_validate_ignores_missing_optional_column() -> None:
    schema = SchemaConfig(columns={"name": ColumnRule(required=False)})
    df = pd.DataFrame({"age": [24]})

    assert validate(df, schema) == []


def test_validate_reports_dtype_mismatch() -> None:
    schema = SchemaConfig(columns={"age": ColumnRule(dtype="string")})
    df = pd.DataFrame({"age": [24, 31]})

    issues = validate(df, schema)

    assert any("expected 'string'" in issue for issue in issues)


def test_validate_reports_null_violation() -> None:
    schema = SchemaConfig(columns={"name": ColumnRule(nullable=False)})
    df = pd.DataFrame({"name": ["Max", None]})

    issues = validate(df, schema)

    assert any("not nullable" in issue for issue in issues)


def test_validate_clean_dataframe_has_no_issues() -> None:
    schema = SchemaConfig(
        columns={"name": ColumnRule(required=True, dtype="string", nullable=False)}
    )
    df = pd.DataFrame({"name": ["Max", "Anna"]})

    assert validate(df, schema) == []

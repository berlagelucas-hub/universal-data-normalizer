from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pandas as pd

_DTYPE_CHECKS = {
    "string": pd.api.types.is_string_dtype,
    "integer": pd.api.types.is_integer_dtype,
    "float": pd.api.types.is_float_dtype,
    "boolean": pd.api.types.is_bool_dtype,
    "datetime": pd.api.types.is_datetime64_any_dtype,
}


@dataclass(frozen=True)
class ColumnRule:
    required: bool = True
    dtype: str | None = None
    nullable: bool = True


@dataclass(frozen=True)
class SchemaConfig:
    columns: dict[str, ColumnRule]

    @classmethod
    def from_file(cls, path: Path) -> SchemaConfig:
        """
        Load a schema/validation config from JSON.

        Expected shape:
            {
              "columns": {
                "first_name": {"required": true, "dtype": "string", "nullable": false}
              }
            }

        Raises:
            ValueError:
                If the file is not a JSON object with a "columns" mapping.
        """

        data = json.loads(Path(path).read_text(encoding="utf-8"))

        if not isinstance(data, dict) or not isinstance(data.get("columns"), dict):
            raise ValueError(
                f"Invalid schema file '{path}': expected a JSON object with a "
                '"columns" mapping of column name -> rule.'
            )

        columns = {
            name: ColumnRule(
                required=rule.get("required", True),
                dtype=rule.get("dtype"),
                nullable=rule.get("nullable", True),
            )
            for name, rule in data["columns"].items()
        }

        return cls(columns=columns)


def validate(df: pd.DataFrame, schema: SchemaConfig) -> list[str]:
    """Check a DataFrame against a schema and return a list of issue messages."""

    issues: list[str] = []

    for name, rule in schema.columns.items():
        if name not in df.columns:
            if rule.required:
                issues.append(f"Missing required column '{name}'")
            continue

        series = cast("pd.Series", df[name])

        if rule.dtype:
            check = _DTYPE_CHECKS.get(rule.dtype)
            if check is not None and not check(series):
                issues.append(
                    f"Column '{name}' has dtype '{series.dtype}', "
                    f"expected '{rule.dtype}'"
                )

        null_mask = series.isna()
        if not rule.nullable and bool(null_mask.any()):
            null_count = len(series) - int(series.count())
            issues.append(
                f"Column '{name}' contains {null_count} null value(s) "
                "but is marked as not nullable"
            )

    return issues

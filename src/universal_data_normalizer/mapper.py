from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


def _normalize_name(name: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[\s-]+", "_", name.strip().lower()))


def _fold_name(name: str) -> str:
    """Collapse a name to bare lowercase alphanumerics, for mapping lookups.

    Keeps "firstname" in a mapping file matching a "First Name" or
    "first_name" column header, since users writing mapping keys by hand
    cannot be expected to guess the exact separator style of every source.
    """
    return re.sub(r"[^a-z0-9]", "", name.lower())


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to snake_case."""
    df = df.copy()
    df.columns = [_normalize_name(column) for column in df.columns]
    return df


def apply_mapping(df: pd.DataFrame, mapping: dict[str, str] | None) -> pd.DataFrame:
    """
    Rename columns according to an explicit source -> target mapping.

    Matching is whitespace/case/separator-insensitive against the mapping
    keys, so a mapping entry written as {"firstname": "first_name"} also
    matches a column header of "First Name". Columns not covered by the
    mapping are left untouched here; normalize_columns() handles the rest.
    """

    if not mapping:
        return df

    lookup = {_fold_name(source): target for source, target in mapping.items()}

    rename = {
        column: lookup[_fold_name(column)]
        for column in df.columns
        if _fold_name(column) in lookup
    }

    if not rename:
        return df

    return df.rename(columns=rename)


def load_mapping(path: Path) -> dict[str, str]:
    """
    Load a column-mapping JSON file (source column name -> target name).

    Raises:
        ValueError:
            If the file does not contain a JSON object of string pairs.
    """

    data = json.loads(Path(path).read_text(encoding="utf-8"))

    if not isinstance(data, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in data.items()
    ):
        raise ValueError(
            f"Invalid mapping file '{path}': expected a JSON object mapping "
            "source column names to target column names (string -> string)."
        )

    return data

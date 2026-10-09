from __future__ import annotations

import pandas as pd

from .mapper import apply_mapping, normalize_columns


def transform(df: pd.DataFrame, mapping: dict[str, str] | None = None) -> pd.DataFrame:
    """
    Apply all transformations.

    The explicit mapping (if any) is applied first so it can target the
    original, unnormalized column names; automatic snake_case normalization
    then covers everything the mapping did not rename.
    """

    df = apply_mapping(df, mapping)
    df = normalize_columns(df)

    return df

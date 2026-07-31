import pandas as pd

from .mapper import normalize_columns

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all transformations."""

    df = normalize_columns(df)

    return df
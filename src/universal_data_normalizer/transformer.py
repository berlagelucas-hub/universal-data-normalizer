import pandas as pd

from .mappings import COLUMN_MAPPING


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns according to the configured mapping."""
    return df.rename(columns=COLUMN_MAPPING)


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all configured transformations.

    The order of transformations is intentional and can be
    extended over time.
    """

    df = rename_columns(df)

    return df
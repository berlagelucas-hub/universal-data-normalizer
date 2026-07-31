import pandas as pd
import re

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = [
        re.sub(r"_+", "_", re.sub(r"[\s-]+", "_", column.strip().lower()))
        for column in df.columns
    ]

    return df
from pathlib import Path

from collections.abc import Callable
import pandas as pd


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame as CSV."""
    df.to_csv(path, index=False)


def write_json(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame as JSON."""
    df.to_json(path, orient="records", indent=4)


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame as Parquet."""
    df.to_parquet(path, index=False)


WRITERS: dict[str, Callable[[pd.DataFrame, Path], None]] = {
    ".csv": write_csv,
    ".json": write_json,
    ".parquet": write_parquet,
    ".pq": write_parquet,
}


def write_file(df: pd.DataFrame, path: Path) -> None:
    """
    Write a DataFrame based on the file extension.

    Raises:
        ValueError:
            If the output format is not supported.
    """

    path = Path(path)

    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        writer = WRITERS[path.suffix.lower()]
    except KeyError:
        supported = ", ".join(sorted(WRITERS))
        raise ValueError(
            f"Unsupported file format '{path.suffix}'. "
            f"Supported formats: {supported}"
        ) from None

    writer(df, path)
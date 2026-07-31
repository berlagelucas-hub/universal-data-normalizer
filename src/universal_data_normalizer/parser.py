from pathlib import Path

from collections.abc import Callable
import pandas as pd


def read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV file into a DataFrame."""
    return pd.read_csv(path, sep=None, engine="python")


def read_json(path: Path) -> pd.DataFrame:
    """Read a JSON file into a DataFrame."""
    return pd.read_json(path)


def read_parquet(path: Path) -> pd.DataFrame:
    """Read a Parquet file into a DataFrame."""
    return pd.read_parquet(path)


READERS: dict[str, Callable[[Path], pd.DataFrame]] = {
    ".csv": read_csv,
    ".json": read_json,
    ".parquet": read_parquet,
    ".pq": read_parquet,
}


def read_file(path: Path) -> pd.DataFrame:
    """
    Read a file based on its extension.

    Raises:
        FileNotFoundError:
            If the file does not exist.
        ValueError:
            If the file extension is not supported.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Expected a file but got: {path}")

    try:
        reader = READERS[path.suffix.lower()]
    except KeyError:
        supported = ", ".join(sorted(READERS))
        raise ValueError(
            f"Unsupported file format '{path.suffix}'. "
            f"Supported formats: {supported}"
        ) from None

    return reader(path)
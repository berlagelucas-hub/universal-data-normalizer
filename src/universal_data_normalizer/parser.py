from __future__ import annotations

import csv
from collections.abc import Callable
from pathlib import Path

import pandas as pd


def _detect_csv_delimiter(path: Path) -> str:
    """
    Detect the delimiter of a CSV file.

    First uses csv.Sniffer. If detection fails, falls back to a list of
    common delimiters.

    Raises:
        ValueError:
            If no suitable delimiter can be determined.
    """

    sample = path.read_text(encoding="utf-8", errors="ignore")[:4096]

    try:
        dialect = csv.Sniffer().sniff(sample)
        return dialect.delimiter
    except csv.Error:
        pass

    common_delimiters = (";", ",", "\t", "|")

    counts = {
        delimiter: sample.count(delimiter)
        for delimiter in common_delimiters
    }

    best_delimiter, count = max(
        counts.items(),
        key=lambda item: item[1],
    )

    if count > 0:
        return best_delimiter

    raise ValueError(
        f"Could not detect a CSV delimiter in '{path.name}'. "
        "The file does not appear to contain any common delimiters "
        "(;, ,, \\t, |). Is it a valid CSV file?"
    )


def read_csv(path: Path) -> pd.DataFrame:
    """
    Read a CSV file into a DataFrame.

    The delimiter is detected automatically.
    """

    delimiter = _detect_csv_delimiter(path)

    return pd.read_csv(
        path,
        sep=delimiter,
        engine="python",
    )


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
from __future__ import annotations

import csv
from collections.abc import Callable, Iterable
from pathlib import Path

import pandas as pd


_COMMON_DELIMITERS = (";", ",", "\t", "|")
_DEFAULT_DELIMITER = ","


def _detect_csv_delimiter(path: Path) -> str:
    """
    Detect the delimiter of a CSV file.

    First uses csv.Sniffer, restricted to a whitelist of plausible
    delimiter characters: left unrestricted, Sniffer can latch onto an
    arbitrary letter that happens to repeat in a consistent column position
    (e.g. mistaking "a" for the delimiter in a single-column file containing
    "name"/"Max"), silently shredding otherwise valid data. If Sniffer can't
    decide, falls back to counting occurrences of the whitelisted
    delimiters. A file with none of them is treated as a single column and
    defaults to a comma, since there is nothing to split either way.
    """

    sample = path.read_text(encoding="utf-8", errors="ignore")[:4096]

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(_COMMON_DELIMITERS))
        return dialect.delimiter
    except csv.Error:
        pass

    counts = {delimiter: sample.count(delimiter) for delimiter in _COMMON_DELIMITERS}

    best_delimiter, count = max(
        counts.items(),
        key=lambda item: item[1],
    )

    return best_delimiter if count > 0 else _DEFAULT_DELIMITER


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


def read_txt(path: Path) -> pd.DataFrame:
    """
    Read a plain .txt export.

    Enterprise ".txt" drops come in two common shapes: delimited text (tab,
    pipe, semicolon - effectively CSV under a different extension) or
    fixed-width positional records (classic mainframe/legacy exports with no
    delimiter at all, columns aligned by character position). Delimited
    text is tried first since it's deterministic and far more common; if
    none of the common delimiters actually occur in the file, this falls
    back to pandas' fixed-width reader with inferred column boundaries,
    which is a best-effort heuristic rather than a guarantee.
    """

    sample = path.read_text(encoding="utf-8", errors="ignore")[:4096]

    if any(delimiter in sample for delimiter in _COMMON_DELIMITERS):
        return read_csv(path)

    return pd.read_fwf(path, colspecs="infer")


def read_json(path: Path) -> pd.DataFrame:
    """Read a JSON file into a DataFrame."""
    return pd.read_json(path)


def read_parquet(path: Path) -> pd.DataFrame:
    """Read a Parquet file into a DataFrame."""
    return pd.read_parquet(path)


def read_excel(path: Path) -> pd.DataFrame:
    """Read the first sheet of an Excel workbook into a DataFrame."""
    return pd.read_excel(path, engine="openpyxl")


def read_xml(path: Path) -> pd.DataFrame:
    """
    Read an XML file into a DataFrame.

    Expects a flat, repeating-record shape (e.g. <root><record><field>...),
    which covers typical ERP/SAP-style exports. Uses the stdlib etree
    backend so no extra XML library (e.g. lxml) is required.
    """
    return pd.read_xml(path, parser="etree")


def read_jsonl(path: Path) -> pd.DataFrame:
    """Read a JSON Lines / NDJSON file (one JSON object per line) into a DataFrame."""
    return pd.read_json(path, lines=True)


READERS: dict[str, Callable[[Path], pd.DataFrame]] = {
    ".csv": read_csv,
    ".json": read_json,
    ".jsonl": read_jsonl,
    ".ndjson": read_jsonl,
    ".parquet": read_parquet,
    ".pq": read_parquet,
    ".txt": read_txt,
    ".xlsx": read_excel,
    ".xml": read_xml,
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
            f"Unsupported file format '{path.suffix}'. Supported formats: {supported}"
        ) from None

    return reader(path)


def discover_input_files(paths: Iterable[Path], pattern: str = "*") -> list[Path]:
    """
    Resolve a mix of files and directories into a flat, sorted list of files.

    Directories are expanded (non-recursively) using `pattern`, keeping only
    files with a supported extension; files are matched case-insensitively
    on extension so a stray ".CSV" is still picked up. A path passed
    explicitly (not inside a directory) is kept as-is even with an
    unsupported extension, so the error surfaces later, per file, instead of
    silently skipping something the user asked for by name.
    """

    files: list[Path] = []

    for path in paths:
        path = Path(path)

        if path.is_dir():
            matched = sorted(
                entry
                for entry in path.glob(pattern)
                if entry.is_file() and entry.suffix.lower() in READERS
            )
            files.extend(matched)
        else:
            files.append(path)

    return files

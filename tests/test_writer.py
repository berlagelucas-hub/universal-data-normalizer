from pathlib import Path

import pandas as pd
import pytest

from universal_data_normalizer.writer import write_file


@pytest.mark.parametrize(
    "extension", ["csv", "json", "jsonl", "ndjson", "parquet", "xlsx", "xml"]
)
def test_write_file_round_trips(tmp_path: Path, extension: str) -> None:
    df = pd.DataFrame({"name": ["Max"], "age": [24]})
    path = tmp_path / f"data.{extension}"

    write_file(df, path)

    assert path.exists()


def test_write_file_creates_missing_parent_directories(tmp_path: Path) -> None:
    df = pd.DataFrame({"name": ["Max"]})
    path = tmp_path / "nested" / "dir" / "data.csv"

    write_file(df, path)

    assert path.exists()


def test_write_file_unsupported_extension(tmp_path: Path) -> None:
    df = pd.DataFrame({"name": ["Max"]})

    with pytest.raises(ValueError, match="Unsupported file format"):
        write_file(df, tmp_path / "data.txt")

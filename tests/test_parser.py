import csv
from pathlib import Path

import pandas as pd
import pytest

from universal_data_normalizer.parser import (
    _detect_csv_delimiter,
    discover_input_files,
    read_file,
)


@pytest.mark.parametrize("delimiter", [",", ";", "\t", "|"])
def test_read_csv_detects_common_delimiters(tmp_path: Path, delimiter: str) -> None:
    path = tmp_path / "data.csv"
    path.write_text(
        f"name{delimiter}age\nMax{delimiter}24\nAnna{delimiter}31\n",
        encoding="utf-8",
    )

    df = read_file(path)

    assert list(df.columns) == ["name", "age"]
    assert len(df) == 2


def test_read_json(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text('[{"name": "Max", "age": 24}]', encoding="utf-8")

    df = read_file(path)

    assert list(df.columns) == ["name", "age"]
    assert len(df) == 1


def test_read_parquet(tmp_path: Path) -> None:
    path = tmp_path / "data.parquet"
    pd.DataFrame({"name": ["Max"], "age": [24]}).to_parquet(path, index=False)

    df = read_file(path)

    assert list(df.columns) == ["name", "age"]


def test_read_excel(tmp_path: Path) -> None:
    path = tmp_path / "data.xlsx"
    pd.DataFrame({"name": ["Max"], "age": [24]}).to_excel(
        path, index=False, engine="openpyxl"
    )

    df = read_file(path)

    assert list(df.columns) == ["name", "age"]


def test_detect_csv_delimiter_falls_back_when_sniffer_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        csv.Sniffer,
        "sniff",
        lambda self, sample, delimiters=None: (_ for _ in ()).throw(
            csv.Error("no delimiter")
        ),
    )
    path = tmp_path / "data.csv"
    path.write_text("a;b;c\n1;2;3\n", encoding="utf-8")

    assert _detect_csv_delimiter(path) == ";"


def test_detect_csv_delimiter_defaults_to_comma_without_any_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        csv.Sniffer,
        "sniff",
        lambda self, sample, delimiters=None: (_ for _ in ()).throw(
            csv.Error("no delimiter")
        ),
    )
    path = tmp_path / "data.csv"
    path.write_text("nodelimitershere\n", encoding="utf-8")

    assert _detect_csv_delimiter(path) == ","


def test_read_csv_handles_single_column_file(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text("name\nMax\nAnna\n", encoding="utf-8")

    df = read_file(path)

    assert list(df.columns) == ["name"]
    assert df["name"].tolist() == ["Max", "Anna"]


def test_read_file_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Expected a file"):
        read_file(tmp_path)


def test_read_file_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_file(tmp_path / "missing.csv")


def test_read_file_unsupported_extension(tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("irrelevant", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file format"):
        read_file(path)


def test_discover_input_files_expands_directory(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (tmp_path / "b.json").write_text("[]", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("nope", encoding="utf-8")

    files = discover_input_files([tmp_path])

    assert sorted(f.name for f in files) == ["a.csv", "b.json"]


def test_discover_input_files_keeps_explicit_unsupported_file(tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("irrelevant", encoding="utf-8")

    files = discover_input_files([path])

    assert files == [path]


def test_discover_input_files_mixes_files_and_directories(tmp_path: Path) -> None:
    directory = tmp_path / "subdir"
    directory.mkdir()
    (directory / "a.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    explicit_file = tmp_path / "b.json"
    explicit_file.write_text("[]", encoding="utf-8")

    files = discover_input_files([directory, explicit_file])

    assert files == [directory / "a.csv", explicit_file]

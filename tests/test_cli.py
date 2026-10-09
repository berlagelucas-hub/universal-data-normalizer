import json
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from universal_data_normalizer.cli import RunConfig, _resolve_output_path, app

runner = CliRunner()


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    path = tmp_path / "people.csv"
    path.write_text(
        "First Name,Last Name,age\nMax,Müller,24\nAnna,Schmidt,31\n",
        encoding="utf-8",
    )
    return path


def test_normalize_single_file_writes_output(tmp_path: Path, csv_file: Path) -> None:
    out_dir = tmp_path / "out"

    result = runner.invoke(
        app, [str(csv_file), "--output-dir", str(out_dir), "--format", "parquet"]
    )

    assert result.exit_code == 0, result.output
    output_path = out_dir / "people.parquet"
    assert output_path.exists()

    df = pd.read_parquet(output_path)
    assert list(df.columns) == ["first_name", "last_name", "age"]


def test_normalize_batch_directory(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    (in_dir / "a.csv").write_text("name,age\nMax,24\n", encoding="utf-8")
    (in_dir / "b.csv").write_text("name,age\nAnna,31\n", encoding="utf-8")
    out_dir = tmp_path / "out"

    result = runner.invoke(
        app, [str(in_dir), "--output-dir", str(out_dir), "--format", "csv"]
    )

    assert result.exit_code == 0, result.output
    assert (out_dir / "a.csv").exists()
    assert (out_dir / "b.csv").exists()


def test_resolve_output_path_falls_back_to_numeric_suffix(tmp_path: Path) -> None:
    config = RunConfig(
        output_dir=tmp_path,
        output_format="csv",
        mapping=None,
        schema=None,
        strict=False,
    )
    used = {tmp_path / "data.csv", tmp_path / "data_csv.csv"}

    result = _resolve_output_path(Path("somewhere/data.csv"), config, used)

    assert result == tmp_path / "data_2.csv"


def test_normalize_disambiguates_colliding_output_stems(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    (in_dir / "data.csv").write_text("name\nMax\n", encoding="utf-8")
    (in_dir / "data.json").write_text('[{"name": "Anna"}]', encoding="utf-8")
    out_dir = tmp_path / "out"

    result = runner.invoke(
        app, [str(in_dir), "--output-dir", str(out_dir), "--format", "csv"]
    )

    assert result.exit_code == 0, result.output
    outputs = sorted(p.name for p in out_dir.glob("*.csv"))
    assert len(outputs) == 2
    assert outputs == ["data.csv", "data_json.csv"]

    first = pd.read_csv(out_dir / "data.csv")
    second = pd.read_csv(out_dir / "data_json.csv")
    assert set(first["name"]) | set(second["name"]) == {"Max", "Anna"}


def test_normalize_reports_failure_for_missing_file(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"

    result = runner.invoke(
        app,
        [str(tmp_path / "missing.csv"), "--output-dir", str(out_dir), "--quiet"],
    )

    assert result.exit_code == 1


def test_normalize_no_matching_files_exits_with_usage_error(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    out_dir = tmp_path / "out"

    result = runner.invoke(app, [str(empty_dir), "--output-dir", str(out_dir)])

    assert result.exit_code == 2


def test_normalize_unknown_output_format_is_rejected(
    tmp_path: Path, csv_file: Path
) -> None:
    out_dir = tmp_path / "out"

    result = runner.invoke(
        app, [str(csv_file), "--output-dir", str(out_dir), "--format", "yaml"]
    )

    assert result.exit_code != 0


def test_normalize_applies_mapping_file(tmp_path: Path) -> None:
    input_path = tmp_path / "data.json"
    input_path.write_text(
        '[{"firstname": "Max", "geburtsdatum": "1990-01-01"}]', encoding="utf-8"
    )
    mapping_path = tmp_path / "mapping.json"
    mapping_path.write_text(
        json.dumps({"firstname": "first_name", "geburtsdatum": "birth_date"}),
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"

    result = runner.invoke(
        app,
        [
            str(input_path),
            "--output-dir",
            str(out_dir),
            "--format",
            "csv",
            "--mapping",
            str(mapping_path),
        ],
    )

    assert result.exit_code == 0, result.output
    df = pd.read_csv(out_dir / "data.csv")
    assert list(df.columns) == ["first_name", "birth_date"]


def test_normalize_schema_violation_is_warning_by_default(tmp_path: Path) -> None:
    input_path = tmp_path / "data.csv"
    input_path.write_text("name\nMax\n", encoding="utf-8")
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(
        json.dumps({"columns": {"age": {"required": True}}}), encoding="utf-8"
    )
    out_dir = tmp_path / "out"

    result = runner.invoke(
        app,
        [
            str(input_path),
            "--output-dir",
            str(out_dir),
            "--schema",
            str(schema_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (out_dir / "data.parquet").exists()


def test_normalize_schema_violation_fails_in_strict_mode(tmp_path: Path) -> None:
    input_path = tmp_path / "data.csv"
    input_path.write_text("name\nMax\n", encoding="utf-8")
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(
        json.dumps({"columns": {"age": {"required": True}}}), encoding="utf-8"
    )
    out_dir = tmp_path / "out"

    result = runner.invoke(
        app,
        [
            str(input_path),
            "--output-dir",
            str(out_dir),
            "--schema",
            str(schema_path),
            "--strict",
        ],
    )

    assert result.exit_code == 1


def test_normalize_writes_report_file(tmp_path: Path, csv_file: Path) -> None:
    out_dir = tmp_path / "out"
    report_path = tmp_path / "report.json"

    result = runner.invoke(
        app,
        [
            str(csv_file),
            "--output-dir",
            str(out_dir),
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code == 0, result.output
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["total"] == 1
    assert report["succeeded"] == 1
    assert report["files"][0]["status"] == "success"


def test_normalize_invalid_mapping_file_exits_with_config_error(
    tmp_path: Path, csv_file: Path
) -> None:
    mapping_path = tmp_path / "mapping.json"
    mapping_path.write_text("not json", encoding="utf-8")
    out_dir = tmp_path / "out"

    result = runner.invoke(
        app,
        [
            str(csv_file),
            "--output-dir",
            str(out_dir),
            "--mapping",
            str(mapping_path),
        ],
    )

    assert result.exit_code == 2

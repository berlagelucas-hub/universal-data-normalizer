from pathlib import Path

import pytest

from universal_data_normalizer.models import FileResult, RunReport


@pytest.fixture
def report() -> RunReport:
    return RunReport(
        results=[
            FileResult(source=Path("a.csv"), status="success", rows=2, columns=3),
            FileResult(source=Path("b.csv"), status="failed", error="boom"),
        ]
    )


def test_file_result_ok_reflects_status() -> None:
    assert FileResult(source=Path("a.csv"), status="success").ok is True
    assert FileResult(source=Path("a.csv"), status="failed").ok is False


def test_run_report_counts(report: RunReport) -> None:
    assert report.succeeded == 1
    assert report.failed == 1


def test_run_report_to_dict(report: RunReport) -> None:
    data = report.to_dict()

    assert data["total"] == 2
    assert data["succeeded"] == 1
    assert data["failed"] == 1
    assert data["files"][1]["error"] == "boom"


def test_run_report_write_json(tmp_path: Path, report: RunReport) -> None:
    path = tmp_path / "nested" / "report.json"

    report.write_json(path)

    assert path.exists()
    assert '"total": 2' in path.read_text(encoding="utf-8")

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FileResult:
    """Outcome of processing a single input file."""

    source: Path
    output: Path | None = None
    status: str = "pending"  # pending, success, failed
    rows: int = 0
    columns: int = 0
    duration_seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "success"

    def to_dict(self) -> dict:
        return {
            "source": str(self.source),
            "output": str(self.output) if self.output else None,
            "status": self.status,
            "rows": self.rows,
            "columns": self.columns,
            "duration_seconds": round(self.duration_seconds, 4),
            "warnings": self.warnings,
            "error": self.error,
        }


@dataclass
class RunReport:
    """Aggregated outcome of a full normalize run across all input files."""

    results: list[FileResult] = field(default_factory=list)

    @property
    def succeeded(self) -> int:
        return sum(1 for result in self.results if result.ok)

    @property
    def failed(self) -> int:
        return sum(1 for result in self.results if not result.ok)

    def to_dict(self) -> dict:
        return {
            "total": len(self.results),
            "succeeded": self.succeeded,
            "failed": self.failed,
            "files": [result.to_dict() for result in self.results],
        }

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

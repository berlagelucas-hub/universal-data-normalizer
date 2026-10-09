from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from .mapper import load_mapping
from .models import FileResult, RunReport
from .parser import discover_input_files, read_file
from .transformer import transform
from .validator import SchemaConfig, validate
from .writer import WRITERS, write_file

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()

_STAGES = ("read", "transform", "validate", "write")


@dataclass
class RunConfig:
    output_dir: Path
    output_format: str
    mapping: dict[str, str] | None
    schema: SchemaConfig | None
    strict: bool


def _setup_logging(verbose: bool) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(console=console, show_path=False, show_time=False)],
        force=True,
    )
    return logging.getLogger("universal_data_normalizer")


def _resolve_output_path(source: Path, config: RunConfig, used: set[Path]) -> Path:
    """
    Pick a non-colliding output path for `source`.

    Different input files can share a stem (e.g. "customers.csv" and
    "customers.json" side by side), which would otherwise make the second
    file silently overwrite the first file's output. On a collision, the
    original extension is folded into the name instead; if that still
    collides, a numeric suffix guarantees uniqueness.
    """

    candidate = config.output_dir / f"{source.stem}.{config.output_format}"
    if candidate not in used:
        return candidate

    disambiguated = (
        config.output_dir
        / f"{source.stem}_{source.suffix.lstrip('.')}.{config.output_format}"
    )
    if disambiguated not in used:
        return disambiguated

    counter = 2
    while True:
        numbered = config.output_dir / f"{source.stem}_{counter}.{config.output_format}"
        if numbered not in used:
            return numbered
        counter += 1


def _process_file(
    source: Path,
    config: RunConfig,
    used_outputs: set[Path],
    progress: Progress,
    task_id: TaskID,
) -> FileResult:
    result = FileResult(source=source)
    started = time.monotonic()
    output_path = _resolve_output_path(source, config, used_outputs)
    used_outputs.add(output_path)

    try:
        df = read_file(source)
        progress.advance(task_id)

        df = transform(df, mapping=config.mapping)
        progress.advance(task_id)

        if config.schema is not None:
            issues = validate(df, config.schema)
            result.warnings.extend(issues)
            if issues and config.strict:
                raise ValueError("Schema validation failed: " + "; ".join(issues))
        progress.advance(task_id)

        write_file(df, output_path)
        progress.advance(task_id)

        result.output = output_path
        result.rows = len(df)
        result.columns = len(df.columns)
        result.status = "success"
    except Exception as exc:  # noqa: BLE001 - isolate failures per file, by design
        result.status = "failed"
        result.error = str(exc)
        progress.update(task_id, completed=len(_STAGES))
    finally:
        result.duration_seconds = time.monotonic() - started

    return result


def _render_summary(report: RunReport, *, show_table: bool) -> None:
    if show_table:
        table = Table(title="Normalisierungslauf - Zusammenfassung")
        table.add_column("Datei")
        table.add_column("Status")
        table.add_column("Zeilen", justify="right")
        table.add_column("Spalten", justify="right")
        table.add_column("Dauer (s)", justify="right")
        table.add_column("Hinweise")

        for result in report.results:
            status = "[green]OK[/green]" if result.ok else "[red]FEHLER[/red]"
            note = result.error or "; ".join(result.warnings)
            table.add_row(
                result.source.name,
                status,
                str(result.rows),
                str(result.columns),
                f"{result.duration_seconds:.2f}",
                note,
            )

        console.print(table)

    summary = f"{report.succeeded}/{len(report.results)} Dateien erfolgreich"
    if report.failed:
        summary += f", {report.failed} fehlgeschlagen"
    console.print(summary)


@app.command()
def normalize(
    inputs: list[Path] = typer.Argument(
        ...,
        help="Eingabedateien und/oder -verzeichnisse (CSV, JSON, Parquet, XLSX).",
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "-o",
        help="Zielverzeichnis für die normalisierten Dateien.",
    ),
    output_format: str = typer.Option(
        "parquet",
        "--format",
        "-f",
        help="Ausgabeformat: csv, json, parquet oder xlsx.",
    ),
    pattern: str = typer.Option(
        "*",
        "--pattern",
        help="Glob-Muster, mit dem Eingabeverzeichnisse durchsucht werden.",
    ),
    mapping_file: Path | None = typer.Option(
        None,
        "--mapping",
        help="JSON-Datei mit explizitem Spalten-Mapping (Quelle -> Ziel).",
    ),
    schema_file: Path | None = typer.Option(
        None,
        "--schema",
        help="JSON-Datei mit Schema-/Validierungsregeln.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Schema-Verstöße als Fehler behandeln statt als Hinweis.",
    ),
    report_file: Path | None = typer.Option(
        None,
        "--report",
        help="Pfad, unter dem ein JSON-Laufbericht gespeichert wird.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Fortschrittsbalken und Tabelle unterdrücken (z. B. für CI-Logs).",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Ausführliches Logging aktivieren.",
    ),
) -> None:
    """Normalisiert eine oder mehrere Datenquellen in ein einheitliches, offenes Format."""

    log = _setup_logging(verbose)

    normalized_format = output_format.lower().lstrip(".")
    if f".{normalized_format}" not in WRITERS:
        supported = ", ".join(sorted(ext.lstrip(".") for ext in WRITERS))
        raise typer.BadParameter(
            f"Unbekanntes Ausgabeformat '{output_format}'. Unterstützt: {supported}"
        )

    try:
        mapping = load_mapping(mapping_file) if mapping_file else None
        schema = SchemaConfig.from_file(schema_file) if schema_file else None
    except (OSError, ValueError) as exc:
        console.print(f"[red]Konfigurationsfehler:[/red] {exc}")
        raise typer.Exit(code=2) from None

    files = discover_input_files(inputs, pattern=pattern)
    if not files:
        console.print("[red]Keine passenden Eingabedateien gefunden.[/red]")
        raise typer.Exit(code=2)

    output_dir.mkdir(parents=True, exist_ok=True)

    config = RunConfig(
        output_dir=output_dir,
        output_format=normalized_format,
        mapping=mapping,
        schema=schema,
        strict=strict,
    )
    report = RunReport()
    used_outputs: set[Path] = set()

    progress_columns = (
        SpinnerColumn(),
        TextColumn("[bold]{task.fields[filename]}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    )

    with Progress(*progress_columns, console=console, disable=quiet) as progress:
        for source in files:
            task_id = progress.add_task(
                "processing", total=len(_STAGES), filename=source.name
            )
            result = _process_file(source, config, used_outputs, progress, task_id)
            report.results.append(result)

            if result.ok:
                log.debug(
                    "%s -> %s (%d Zeilen)", source.name, result.output, result.rows
                )
            else:
                log.error("%s: %s", source.name, result.error)

    _render_summary(report, show_table=not quiet)

    if report_file:
        report.write_json(report_file)

    if report.failed:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

# Universal Data Normalizer

[![CI](https://github.com/berlagelucas-hub/universal-data-normalizer/actions/workflows/ci.yml/badge.svg)](https://github.com/berlagelucas-hub/universal-data-normalizer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](pyproject.toml)

Ein CLI-Tool, das Tabellendaten aus verschiedenen Quellen (CSV, JSON, JSON
Lines, XML, Excel, Parquet) einlesen, in ein einheitliches Schema bringen und
in ein offenes, Lakehouse-freundliches Format (Parquet) schreiben kann — als
Vorverarbeitungsschicht vor einem Data Lakehouse.

## Features

- **Mehrere Formate**: CSV (mit automatischer Trennzeichen-Erkennung), JSON,
  JSON Lines/NDJSON, XML (z. B. ERP-/SAP-Exporte), Excel (`.xlsx`) und
  Parquet als Ein- und Ausgabeformat; `.txt`-Exporte zusätzlich als
  Eingabeformat (siehe unten).
- **Batch-Verarbeitung**: beliebig viele Dateien und/oder Verzeichnisse in
  einem Lauf, einzeln fehlertolerant (eine fehlerhafte Datei stoppt nicht den
  ganzen Lauf).
- **Spalten-Normalisierung**: automatische snake_case-Vereinheitlichung aller
  Spaltennamen.
- **Explizites Spalten-Mapping**: optionale JSON-Datei, um Quellspalten
  gezielt auf Zielnamen umzubenennen (z. B. `geburtsdatum` -> `birth_date`).
- **Schema-/Datenqualitätsprüfung**: optionale JSON-Schema-Datei zur Prüfung
  von Pflichtspalten, Datentypen und Nullable-Regeln je Lauf.
- **Transparenz pro Lauf**: Fortschrittsbalken pro Datei, eine
  Zusammenfassungstabelle (Status, Zeilen, Spalten, Dauer, Hinweise) und ein
  optionaler maschinenlesbarer JSON-Laufbericht (`--report`).
- **Saubere Exit-Codes**: `0` bei vollem Erfolg, `1` wenn mindestens eine
  Datei fehlgeschlagen ist, `2` bei Konfigurations-/Eingabefehlern.

## Installation

```bash
uv sync
```

## Nutzung

```bash
# Eine Datei normalisieren
uv run udn examples/input.csv --output-dir out --format parquet

# Mehrere Dateien/Verzeichnisse in einem Lauf (Batch)
uv run udn data/raw --output-dir out --format parquet --pattern "*.csv"

# Mit explizitem Spalten-Mapping und Schema-Validierung
uv run udn examples/input.json \
  --output-dir out \
  --mapping examples/mapping.json \
  --schema examples/schema.json \
  --report out/report.json
```

Alternativ über das Modul: `python -m universal_data_normalizer ...`
(z. B. im Container, siehe `Dockerfile`).

### Mapping-Datei

JSON-Objekt von Quellspalte -> Zielspalte, siehe `examples/mapping.json`.
Der Vergleich ist Groß-/Kleinschreibung-, Leerzeichen- und
Trennzeichen-unabhängig, sodass eine Angabe wie `"firstname"` auch eine
Spalte `"First Name"` trifft.

### Schema-Datei

JSON-Objekt mit Spaltenregeln (`required`, `dtype`, `nullable`), siehe
`examples/schema.json`. Verstöße werden standardmäßig als Hinweise im
Laufbericht aufgeführt; mit `--strict` gelten sie als Fehler für die
jeweilige Datei.

### `.txt`-Dateien

Enterprise-`.txt`-Exporte sind in der Praxis fast immer eines von zwei
Dingen: getrennter Text (Tab/Pipe/Semikolon — faktisch CSV mit anderer
Endung) oder ein Fixed-Width-Export ohne jedes Trennzeichen (klassischer
Mainframe-/Altsystem-Export, Spalten durch Zeichenposition definiert). Der
Normalizer erkennt zuerst, ob eines der bekannten Trennzeichen vorkommt
(dann wie CSV gelesen); andernfalls wird mit pandas' Fixed-Width-Reader
(`colspecs="infer"`) versucht, die Spaltenbreiten aus dem Inhalt
abzuleiten. Das ist ein **Best-Effort-Verfahren**, kein Garant — bei sehr
kurzen oder unregelmäßigen Dateien kann die Spaltenerkennung danebenliegen;
im Zweifel das Ergebnis prüfen. `.txt` ist nur Eingabe-, kein
Ausgabeformat, da es kein eindeutiges offenes Zielformat beschreibt.

### Umfangreiches Beispiel

`examples/advanced/` bildet einen realistischen Konsolidierungsfall nach:
Kundenstammdaten aus vier unterschiedlich benannten/strukturierten
Quellsystemen (deutscher Webshop als CSV, englische Partner-API als JSON,
Partner-Excel mit Kürzeln, ERP/SAP-Export als XML) plus einem echten
Mainframe-Fixed-Width-Export (`legacy_export.txt`), der zwar technisch
eingelesen wird, aber keine der erwarteten Zielspalten enthält — die
Schema-Prüfung macht das pro Datei sichtbar, ohne den gesamten Lauf
abzubrechen:

```bash
uv run udn examples/advanced/data \
  --output-dir out \
  --mapping examples/advanced/mapping.json \
  --schema examples/advanced/schema.json \
  --report out/report.json
```

## Entwicklung

```bash
uv run pytest --cov=src            # Tests inkl. Coverage
uv run ruff check . && uv run ruff format --check .
uv run pyright                     # Statische Typprüfung
uv run bandit -r src               # Sicherheitsanalyse
```

## Tech-Stack

- uv, Ruff, Pyright, Bandit, Pytest/pytest-cov
- Typer + Rich (CLI, Fortschrittsanzeige)
- pandas + pyarrow + openpyxl (Ein-/Ausgabe)
- GitHub Actions (CI), Podman/Docker (Container-Build)
- pre-commit

## Roadmap

- [x] uv, Ruff, Pyright, Bandit
- [x] Pytest mit Coverage
- [x] GitHub Actions CI
- [x] Container-Build (Podman/Docker)
- [x] Batch-Verarbeitung mehrerer Dateien/Verzeichnisse
- [x] Excel-Unterstützung
- [x] Spalten-Mapping-Konfiguration
- [x] Schema-/Datenqualitätsprüfung
- [x] Lauf-Report (Konsole + JSON)
- [ ] Parallele Verarbeitung großer Dateimengen
- [ ] Partitionierte Parquet-Ausgabe für sehr große Datasets

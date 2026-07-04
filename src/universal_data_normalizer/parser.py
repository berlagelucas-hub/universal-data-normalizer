from pathlib import Path
import pandas as pd


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=None, engine="python")


def read_json(path: Path) -> pd.DataFrame:
    return pd.read_json(path)


def read_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


READERS = {
    ".csv": read_csv,
    ".json": read_json,
    ".parquet": read_parquet,
    ".pq": read_parquet,
}


def read_file(path: Path) -> pd.DataFrame:
    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")

    try:
        reader = READERS[path.suffix.lower()]
    except KeyError:
        raise ValueError(
            f"Dateiformat '{path.suffix}' wird nicht unterstützt."
        ) from None

    return reader(path)

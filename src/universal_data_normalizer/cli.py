from pathlib import Path

import typer

from .parser import read_file
from .transformer import transform
from .writer import write_file

app = typer.Typer()


@app.command()
def normalize(
    input_file: Path,
    output_file: Path,
):
    df = read_file(input_file)
    df = transform(df)
    write_file(df, output_file)


if __name__ == "__main__":
    app()
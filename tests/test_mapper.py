from pathlib import Path

import pandas as pd
import pytest

from universal_data_normalizer.mapper import (
    apply_mapping,
    load_mapping,
    normalize_columns,
)


def test_normalize_columns_handles_spacing_case_and_separators() -> None:
    df = pd.DataFrame(
        columns=["First Name", "last-name", "  weird__spacing  ", "ALREADY_SNAKE"]
    )

    result = normalize_columns(df)

    assert list(result.columns) == [
        "first_name",
        "last_name",
        "weird_spacing",
        "already_snake",
    ]


def test_apply_mapping_matches_case_and_whitespace_insensitively() -> None:
    df = pd.DataFrame(columns=["First Name", "geburtsdatum"])
    mapping = {"firstname": "first_name", "geburtsdatum": "birth_date"}

    result = apply_mapping(df, mapping)

    assert list(result.columns) == ["first_name", "birth_date"]


def test_apply_mapping_leaves_unmatched_columns_untouched() -> None:
    df = pd.DataFrame(columns=["age"])

    result = apply_mapping(df, {"firstname": "first_name"})

    assert list(result.columns) == ["age"]


def test_apply_mapping_with_none_is_a_no_op() -> None:
    df = pd.DataFrame(columns=["age"])

    result = apply_mapping(df, None)

    assert list(result.columns) == ["age"]


def test_load_mapping_reads_valid_file(tmp_path: Path) -> None:
    path = tmp_path / "mapping.json"
    path.write_text('{"firstname": "first_name"}', encoding="utf-8")

    assert load_mapping(path) == {"firstname": "first_name"}


@pytest.mark.parametrize(
    "content",
    [
        "[]",
        '{"firstname": 1}',
        '{"firstname": null}',
    ],
)
def test_load_mapping_rejects_invalid_shape(tmp_path: Path, content: str) -> None:
    path = tmp_path / "mapping.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid mapping file"):
        load_mapping(path)

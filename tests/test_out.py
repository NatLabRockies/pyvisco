"""Tests for CSV output utilities."""

from __future__ import annotations

import pandas as pd

from pyvisco import out


def _example_frame():
    df = pd.DataFrame({"f": [1.0, 10.0, 100.0], "E_stor": [1e3, 2e3, 3e3]})
    units = {"f": "Hz", "E_stor": "MPa"}
    return df, units


def test_add_units_creates_multiindex_header():
    df, units = _example_frame()
    df_out = out.add_units(df, units)
    assert isinstance(df_out.columns, pd.MultiIndex)
    assert df_out.columns.get_level_values(1).tolist() == ["Hz", "MPa"]
    # Values are preserved
    assert df_out.iloc[0, 0] == 1.0


def test_to_csv_returns_string_when_no_filepath():
    df, units = _example_frame()
    csv_text = out.to_csv(df, units)
    assert isinstance(csv_text, str)
    assert "Hz" in csv_text and "MPa" in csv_text


def test_to_csv_writes_to_disk(tmp_path):
    df, units = _example_frame()
    target = tmp_path / "out.csv"
    result = out.to_csv(df, units, filepath=str(target))
    assert result is None
    assert target.exists()
    assert target.stat().st_size > 0


def test_add_units_with_index_label_names_multiindex():
    df, units = _example_frame()
    df_out = out.add_units(df, units, index_label="Quantity")
    assert df_out.columns.names == ["Quantity", "-"]
    assert df_out.columns.get_level_values(0).tolist() == ["f", "E_stor"]
    assert df_out.columns.get_level_values(1).tolist() == ["Hz", "MPa"]


def test_to_csv_with_index_label_includes_index_column(tmp_path):
    """With index_label set, the row index must be written to the CSV."""
    df, units = _example_frame()
    df.index.name = "row"
    target = tmp_path / "out_with_index.csv"
    out.to_csv(df, units, index_label="Quantity", filepath=str(target))

    text = target.read_text()
    # Header row carries the index_label as the first column name
    assert text.splitlines()[0].startswith("Quantity,")
    # The row indices (0, 1, 2) should appear in the first column of the data rows
    body_first_col = [line.split(",")[0] for line in text.splitlines()[3:]]
    assert body_first_col == ["0", "1", "2"]


def test_to_csv_buffer_with_index_label_includes_index():
    df, units = _example_frame()
    csv_text = out.to_csv(df, units, index_label="Quantity")
    assert csv_text.splitlines()[0].startswith("Quantity,")

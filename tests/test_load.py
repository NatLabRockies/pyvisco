"""Tests for the data loading utilities."""
from __future__ import annotations

from pyvisco import load


def test_conventions_E_contains_expected_keys():
    conv = load.conventions("E")
    assert "E_relax" in conv
    assert "E_stor" in conv
    assert "E_loss" in conv


def test_conventions_G_contains_expected_keys():
    conv = load.conventions("G")
    assert "G_relax" in conv


def test_user_master_time_csv(examples_dir):
    """Load the bundled time-domain master curve example."""
    path = examples_dir / "time_user_master.csv"
    data = load.file(str(path))
    df_master, units = load.user_master(data, domain="time", RefT=25.0, modul="E")

    assert df_master.domain == "time"
    assert df_master.modul == "E"
    assert df_master.RefT == 25.0
    assert "E_relax" in df_master.columns
    assert "t" in df_master.columns
    assert "f" in df_master.columns
    assert len(df_master) > 0
    assert "E_relax" in units

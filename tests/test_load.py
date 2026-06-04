"""Tests for the data loading utilities."""

from __future__ import annotations

import io

import pandas as pd
import pytest

from pyvisco import load

# ---------------------------------------------------------------------------
# conventions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("modul", "expected_keys"),
    [
        ("E", ("E_relax", "E_stor", "E_loss", "E_comp", "E_0", "E_inf", "E_i")),
        ("G", ("G_relax", "G_stor", "G_loss", "G_comp", "G_0", "G_inf", "G_i")),
    ],
)
def test_conventions_contains_expected_keys(modul, expected_keys):
    conv = load.conventions(modul)
    for key in expected_keys:
        assert key in conv
    # Domain-independent quantities are always present
    for key in ("f", "t", "omega", "T", "tau_i", "alpha_i", "log_aT"):
        assert key in conv


# ---------------------------------------------------------------------------
# user_master (frequency- and time-domain master curves)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("filename", "domain", "ref_T"),
    [
        ("time_user_master.csv", "time", 25.0),
        ("freq_user_master.csv", "freq", -5.0),
    ],
)
def test_user_master_csv(sample_data_dir, filename, domain, ref_T):
    data = load.file(str(sample_data_dir / filename))
    df_master, units = load.user_master(data, domain=domain, RefT=ref_T, modul="E")

    assert df_master.domain == domain
    assert df_master.modul == "E"
    assert df_master.RefT == ref_T
    # Both domains derive these auxiliary columns
    for col in ("f", "t", "omega"):
        assert col in df_master.columns
    # Domain-specific modulus column
    expected_modulus = "E_relax" if domain == "time" else "E_stor"
    assert expected_modulus in df_master.columns
    assert len(df_master) > 0
    assert expected_modulus in units


# ---------------------------------------------------------------------------
# user_raw (multi-temperature raw measurements)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("filename", "domain", "extra_cols"),
    [
        ("freq_user_raw.csv", "freq", ("f_set", "E_stor", "E_loss")),
        ("time_user_raw.csv", "time", ("t_set", "f_set", "E_relax")),
    ],
)
def test_user_raw_csv(sample_data_dir, filename, domain, extra_cols):
    data = load.file(str(sample_data_dir / filename))
    df_raw, arr_RefT, _units = load.user_raw(data, domain=domain, modul="E")

    assert df_raw.domain == domain
    assert df_raw.modul == "E"
    for col in (*extra_cols, "T", "Set", "T_round"):
        assert col in df_raw.columns
    assert len(arr_RefT) >= 2
    assert df_raw["Set"].nunique() == len(arr_RefT)


def test_user_shift_csv(sample_data_dir):
    """Load user-provided shift factors."""
    path = sample_data_dir / "time_user_raw__shift_factors.csv"
    data = load.file(str(path))
    df_aT = load.user_shift(data)

    assert {"T", "log_aT"}.issubset(df_aT.columns)
    assert len(df_aT) > 0


# ---------------------------------------------------------------------------
# Eplexor_raw / Eplexor_master (Excel files from Netzsch Gabo EPLEXOR)
# ---------------------------------------------------------------------------


def test_eplexor_raw_xls(sample_data_dir):
    """Load bundled EPLEXOR raw-data Excel file."""
    data = load.file(str(sample_data_dir / "freq_Eplexor_raw.xls"))
    df_raw, arr_RefT, units = load.Eplexor_raw(data, modul="E")

    assert df_raw.domain == "freq"
    assert df_raw.modul == "E"
    for col in ("f_set", "E_stor", "E_loss", "E_comp", "tan_del", "T", "Set", "T_round"):
        assert col in df_raw.columns
    assert len(arr_RefT) >= 2
    assert df_raw["Set"].nunique() == len(arr_RefT)
    # get_units propagates the Pascal unit across all modulus keys
    assert units["E_stor"] == units["E_loss"] == units["E_comp"]


@pytest.mark.parametrize(
    ("filename", "modul"),
    [
        ("freq_Eplexor_master.xls", "E"),
        ("freq_Eplexor_master_shear.xls", "G"),
    ],
)
def test_eplexor_master_xls(sample_data_dir, filename, modul):
    """Load bundled EPLEXOR master-curve Excel files (tensile + shear)."""
    data = load.file(str(sample_data_dir / filename))
    df_master, df_aT, df_WLF, units = load.Eplexor_master(data, modul=modul)

    assert df_master.domain == "freq"
    assert df_master.modul == modul
    for col in ("f", f"{modul}_stor", f"{modul}_loss", f"{modul}_comp", "tan_del", "omega", "t"):
        assert col in df_master.columns
    assert len(df_master) > 0
    # Reference temperature is propagated to the WLF frame
    assert df_WLF.loc[0, "RefT"] == df_master.RefT
    assert set(df_WLF.columns) == {"RefT", "C1", "C2"}
    assert {"T", "log_aT"}.issubset(df_aT.columns)
    assert len(df_aT) > 0


# ---------------------------------------------------------------------------
# get_sets (Eplexor-style set detection)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("num", "expected_sets"),
    [
        # Explicit num: 6 rows split into 3 sets of 2
        (2, [0, 0, 1, 1, 2, 2]),
        # num=0 means auto-detect: the first occurrence of the max f_set value
        # determines the set length. With f_set going 1,10,100,1,10,100 the max
        # appears at index 2, so num is detected as 3 -> 2 sets of 3.
        (0, [0, 0, 0, 1, 1, 1]),
    ],
)
def test_get_sets_grouping(num, expected_sets):
    df = pd.DataFrame({"f_set": [1.0, 10.0, 100.0, 1.0, 10.0, 100.0]})
    df_out = load.get_sets(df, num=num)
    assert df_out["Set"].tolist() == expected_sets


# ---------------------------------------------------------------------------
# get_units (Eplexor vs. user CSV column-name convention)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("domain", "eplexor", "units_in"),
    [
        ("freq", False, {"E_stor": "MPa", "E_loss": "MPa"}),
        ("freq", True, {"E'": "GPa", "E''": "GPa"}),
        ("time", False, {"E_relax": "kPa"}),
    ],
)
def test_get_units_propagates_pascal_unit(domain, eplexor, units_in):
    """get_units must propagate the modulus unit to every modulus key."""
    expected = units_in[next(iter(units_in))]
    conv = load.get_units(units_in, modul="E", domain=domain, Eplexor=eplexor)
    for key in ("E_relax", "E_stor", "E_loss", "E_comp", "E_0", "E_inf", "E_i"):
        assert conv[key] == expected
    # Non-modulus quantities collapse to their first allowed unit
    assert conv["f"] == "Hz"
    assert conv["t"] == "s"


# ---------------------------------------------------------------------------
# check_units (validation error paths)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_units",
    [
        # Wrong unit for a known quantity
        {"E_stor": "psi", "E_loss": "psi"},
        # Mismatched storage / loss units
        {"E_stor": "MPa", "E_loss": "GPa"},
        # Wrong temperature unit
        {"T": "K"},
    ],
)
def test_check_units_raises_on_invalid_input(bad_units):
    with pytest.raises(KeyError):
        load.check_units(bad_units, modul="E")


def test_check_units_accepts_valid_units():
    """A spec-compliant unit dict must not raise."""
    valid = {
        "f": "Hz",
        "t": "s",
        "T": "°C",
        "E_stor": "MPa",
        "E_loss": "MPa",
        "E_relax": "MPa",
        "log_aT": "-",
    }
    load.check_units(valid, modul="E")  # must not raise


# ---------------------------------------------------------------------------
# prep_csv (header parsing)
# ---------------------------------------------------------------------------


def test_prep_csv_parses_two_row_header_and_drops_nans():
    csv = io.BytesIO(b"f,E_stor\nHz,MPa\n1,1000\n10,2000\n,\n")
    df, units = load.prep_csv(csv.getvalue())
    assert list(df.columns) == ["f", "E_stor"]
    assert units == {"f": "Hz", "E_stor": "MPa"}
    # NaN row dropped
    assert len(df) == 2

"""Tests for the master-curve assembly pipeline."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure

from pyvisco import load, master

# ---------------------------------------------------------------------------
# Power-law primitives (pwr_y / pwr_x / fit_pwr)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "e"),
    [
        (2.0, 0.5, 0.0),
        (1.5, -0.3, 1.0),
        (0.8, 1.2, -2.0),
    ],
)
def test_pwr_y_and_pwr_x_are_inverses(a, b, e):
    x = np.array([0.1, 1.0, 10.0, 100.0])
    y = master.pwr_y(x, a, b, e)
    x_recovered = master.pwr_x(y, a, b, e)
    np.testing.assert_allclose(x_recovered, x, rtol=1e-9)


def test_fit_pwr_recovers_constants_from_clean_data():
    a_true, b_true, e_true = 1000.0, -0.5, 50.0
    x = np.geomspace(0.1, 100.0, 30)
    y = master.pwr_y(x, a_true, b_true, e_true)

    popt, _pcov = master.fit_pwr(x, y)
    np.testing.assert_allclose(popt[0], a_true, rtol=1e-4)
    np.testing.assert_allclose(popt[1], b_true, rtol=1e-4)
    np.testing.assert_allclose(popt[2], e_true, atol=1e-3)


# ---------------------------------------------------------------------------
# get_aT / get_curve (TTSP) -- both domains, parametrized over the bundled
# raw sample files
# ---------------------------------------------------------------------------


@pytest.fixture
def time_raw(sample_data_dir):
    data = load.file(str(sample_data_dir / "time_user_raw.csv"))
    return load.user_raw(data, domain="time", modul="E")


@pytest.fixture
def freq_raw_eplexor(sample_data_dir):
    """EPLEXOR raw frequency data exercises the freq branch of get_curve
    including the ``E_comp``/``tan_del`` propagation path."""
    data = load.file(str(sample_data_dir / "freq_Eplexor_raw.xls"))
    return load.Eplexor_raw(data, modul="E")


@pytest.mark.parametrize(
    "raw_fixture",
    ["time_raw", "freq_raw_eplexor"],
)
def test_get_aT_then_get_curve(raw_fixture, request):
    """End-to-end TTSP: get_aT followed by get_curve must return a
    well-formed master curve in both time and frequency domains."""
    df_raw, arr_RefT, _units = request.getfixturevalue(raw_fixture)
    RefT = float(arr_RefT.iloc[len(arr_RefT) // 2])

    df_aT, dshift = master.get_aT(df_raw, RefT)
    assert {"T", "log_aT"}.issubset(df_aT.columns)
    assert len(df_aT) == len(arr_RefT)
    # log_aT is exactly zero at the reference temperature
    assert df_aT.loc[df_aT["T"] == RefT, "log_aT"].iloc[0] == 0.0
    # debug dict contains one entry per shifted temperature
    assert isinstance(dshift, dict)
    assert len(dshift) == len(arr_RefT) - 1

    df_master = master.get_curve(df_raw, df_aT, RefT)
    assert df_master.domain == df_raw.domain
    assert df_master.modul == "E"
    assert df_master.RefT == RefT
    # Common derived columns in both domains
    for col in ("f", "t", "omega"):
        assert col in df_master.columns
    # Domain-specific moduli
    if df_master.domain == "freq":
        for col in ("E_stor", "E_loss"):
            assert col in df_master.columns
    else:
        assert "E_relax" in df_master.columns
    assert len(df_master) > 0


def test_get_curve_freq_propagates_comp_and_tan_del(freq_raw_eplexor):
    """The EPLEXOR raw frame carries E_comp and tan_del -- get_curve must
    forward them to the master frame."""
    df_raw, arr_RefT, _units = freq_raw_eplexor
    RefT = float(arr_RefT.iloc[len(arr_RefT) // 2])
    df_aT, _dshift = master.get_aT(df_raw, RefT)
    df_master = master.get_curve(df_raw, df_aT, RefT)
    assert "E_comp" in df_master.columns
    assert "tan_del" in df_master.columns


# ---------------------------------------------------------------------------
# smooth (median filter)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("filename", "domain", "RefT", "filt_col"),
    [
        ("time_user_master.csv", "time", 25.0, "E_relax_filt"),
        ("freq_user_master.csv", "freq", -5.0, "E_stor_filt"),
    ],
)
def test_smooth_adds_filtered_column(sample_data_dir, filename, domain, RefT, filt_col):
    data = load.file(str(sample_data_dir / filename))
    df_master, _units = load.user_master(data, domain=domain, RefT=RefT, modul="E")
    df_smoothed = master.smooth(df_master, win=3)
    assert filt_col in df_smoothed.columns
    if domain == "freq":
        assert "E_loss_filt" in df_smoothed.columns
    assert len(df_smoothed) == len(df_master)


# ---------------------------------------------------------------------------
# Plot smoke tests -- verify each plot function runs end-to-end on bundled
# sample data and returns a ``matplotlib.figure.Figure``. They do not
# compare pixel output -- they catch import errors, column-name typos,
# and API drift in the plotting layer. The ``Agg`` backend is set in
# ``conftest.py`` so no GUI is opened.
# ---------------------------------------------------------------------------


def test_plot_time(time_master):
    df_master, units = time_master
    fig = master.plot(df_master, units)
    assert isinstance(fig, Figure)
    plt.close(fig)


def test_plot_freq(freq_master):
    df_master, units = freq_master
    fig = master.plot(df_master, units)
    assert isinstance(fig, Figure)
    plt.close(fig)


def test_plot_smooth_time(time_master):
    df_master, units = time_master
    fig = master.plot_smooth(df_master, units)
    assert isinstance(fig, Figure)
    plt.close(fig)


def test_plot_smooth_freq(freq_master):
    df_master, units = freq_master
    fig = master.plot_smooth(df_master, units)
    assert isinstance(fig, Figure)
    plt.close(fig)


def test_plot_shift(raw_and_master):
    """plot_shift must produce a Figure and matching ax-tuple in both domains."""
    df_raw, df_master, _dshift, units = raw_and_master
    fig, ax = master.plot_shift(df_raw, df_master, units)
    assert isinstance(fig, Figure)
    # Time-domain returns a 2-tuple; frequency-domain returns a 4-tuple
    assert len(ax) in (2, 4)
    plt.close(fig)


def test_plot_shift_update(raw_and_master):
    """plot_shift_update reuses the figure/axes returned by plot_shift in
    both the time- and frequency-domain branches."""
    df_raw, df_master, _dshift, units = raw_and_master
    fig, ax = master.plot_shift(df_raw, df_master, units)
    fig2 = master.plot_shift_update(df_master, fig, ax)
    assert fig2 is fig
    plt.close(fig)


def test_plot_shift_debug(raw_and_master, capsys):
    _df_raw, _df_master, dshift, _units = raw_and_master
    master.plot_shift_debug(dshift)
    # plot_shift_debug prints drop-first diagnostics per shifted temperature
    captured = capsys.readouterr()
    assert "ref-drop-first" in captured.out
    plt.close("all")

"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

# Use a non-interactive matplotlib backend so plotting code never opens a window
import matplotlib
import pytest

matplotlib.use("Agg")

from pyvisco import load, master, prony  # noqa: E402  (after matplotlib.use)


@pytest.fixture(scope="session")
def sample_data_dir() -> Path:
    """Path to the bundled sample-data directory."""
    return Path(__file__).resolve().parent.parent / "sample_data"


@pytest.fixture(scope="session")
def tests_data_dir() -> Path:
    """Path to the tests/data directory (test-only fixtures)."""
    return Path(__file__).resolve().parent / "data"


# ---------------------------------------------------------------------------
# Master-curve fixtures shared across multiple test modules.
# ---------------------------------------------------------------------------


@pytest.fixture
def time_master(sample_data_dir):
    """Bundled time-domain user master curve, smoothed."""
    data = load.file(str(sample_data_dir / "time_user_master.csv"))
    df_master, units = load.user_master(data, domain="time", RefT=25.0, modul="E")
    df_master = master.smooth(df_master, win=1)
    return df_master, units


@pytest.fixture
def freq_master(sample_data_dir):
    """Bundled frequency-domain user master curve, smoothed."""
    data = load.file(str(sample_data_dir / "freq_user_master.csv"))
    df_master, units = load.user_master(data, domain="freq", RefT=-5.0, modul="E")
    df_master = master.smooth(df_master, win=5)
    return df_master, units


@pytest.fixture(params=["time", "freq"])
def master_data(request, time_master, freq_master):
    """``(df_master, units)`` parametrized across both domains."""
    return time_master if request.param == "time" else freq_master


@pytest.fixture
def master_with_prony(master_data):
    """``(df_master, units, prony_fit, df_gmaxw)`` parametrized across both
    domains. The Prony ``fit`` call needs ``df_master`` only in the time
    domain."""
    df_master, units = master_data
    df_dis = prony.discretize(df_master, window="round")
    if df_master.domain == "freq":
        prony_fit, df_gmaxw = prony.fit(df_dis)
    else:
        prony_fit, df_gmaxw = prony.fit(df_dis, df_master)
    return df_master, units, prony_fit, df_gmaxw


@pytest.fixture(
    params=[
        ("time_user_raw.csv", "time", "user"),
        ("freq_Eplexor_raw.xls", "freq", "eplexor"),
    ],
    ids=["time-user", "freq-eplexor"],
)
def raw_and_master(request, sample_data_dir):
    """Raw measurement data + assembled master curve, in both domains.

    The frequency variant uses the bundled EPLEXOR ``.xls`` raw sample
    so the ``E_comp``/``tan_del`` propagation path is also exercised.
    """
    filename, domain, source = request.param
    data = load.file(str(sample_data_dir / filename))
    if source == "user":
        df_raw, arr_RefT, units = load.user_raw(data, domain=domain, modul="E")
    else:
        df_raw, arr_RefT, units = load.Eplexor_raw(data, modul="E")
    RefT = float(arr_RefT.iloc[len(arr_RefT) // 2])
    df_aT, dshift = master.get_aT(df_raw, RefT)
    df_master = master.get_curve(df_raw, df_aT, RefT)
    return df_raw, df_master, dshift, units

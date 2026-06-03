"""Round-trip tests for the Prony series fitting pipeline."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

from pyvisco import prony, shift


def test_e_relax_norm_initial_and_long_time():
    """Normalized relaxation modulus must equal 1 at t=0 and 1-sum(alpha) as t -> inf."""
    alpha_i = np.array([0.2, 0.3, 0.1])
    tau_i = np.array([0.01, 1.0, 100.0])

    # t = 0 -> 1
    t = np.array([0.0])
    np.testing.assert_allclose(prony.E_relax_norm(t, alpha_i, tau_i), [1.0], atol=1e-12)

    # t -> very large -> 1 - sum(alpha_i)
    t_large = np.array([1e12])
    np.testing.assert_allclose(
        prony.E_relax_norm(t_large, alpha_i, tau_i),
        [1.0 - alpha_i.sum()],
        atol=1e-12,
    )


def test_time_domain_pipeline_roundtrip(time_master):
    """End-to-end fit on the bundled time-domain master curve.

    Discretizes relaxation times, fits a Prony series, reconstructs the
    Generalized Maxwell response, and asserts the reconstruction matches the
    input data to within a tight tolerance.
    """
    df_master, _units = time_master

    df_dis = prony.discretize(df_master, window="round")
    assert df_dis.nprony > 0
    assert "tau_i" in df_dis.columns

    prony_fit, df_gmaxw = prony.fit(df_dis, df_master)
    df_terms = prony_fit["df_terms"]

    # Basic sanity on the Prony parameters
    assert (df_terms["alpha_i"] >= 0).all()
    assert df_terms["alpha_i"].sum() <= 1.0 + 1e-9
    assert (df_terms["tau_i"] > 0).all()

    # Generalized Maxwell reconstruction columns
    assert "t" in df_gmaxw.columns
    assert "E_relax" in df_gmaxw.columns

    # Evaluate the fitted Prony series directly at the measurement times and
    # check it reproduces the master curve to within a tight relative tolerance.
    alpha_i = df_terms["alpha_i"].values
    tau_i = df_terms["tau_i"].values
    E_0 = prony_fit["E_0"]

    t_meas = df_master["t"].values
    e_meas = df_master["E_relax"].values
    e_recon = E_0 * prony.E_relax_norm(t_meas, alpha_i, tau_i)

    rel_err = np.linalg.norm(e_recon - e_meas) / np.linalg.norm(e_meas)
    assert rel_err < 0.05, f"Prony reconstruction error too large: {rel_err:.3%}"


def test_freq_domain_pipeline_roundtrip(freq_master):
    """End-to-end fit on the bundled frequency-domain master curve."""
    df_master, _units = freq_master

    df_dis = prony.discretize(df_master, window="round")
    assert df_dis.nprony > 0

    prony_fit, df_gmaxw = prony.fit(df_dis)
    df_terms = prony_fit["df_terms"]

    assert (df_terms["alpha_i"] >= 0).all()
    assert df_terms["alpha_i"].sum() <= 1.0 + 1e-9
    assert (df_terms["tau_i"] > 0).all()

    # Generalized Maxwell reconstruction must produce a storage modulus column
    assert "E_stor" in df_gmaxw.columns
    assert "f" in df_gmaxw.columns
    assert len(df_gmaxw) > 0


# ---------------------------------------------------------------------------
# discretize: cover all three window strategies
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("window", ["round", "exact", "min"])
def test_discretize_window_variants_freq(freq_master, window):
    df_master, _units = freq_master
    df_dis = prony.discretize(df_master, window=window)
    assert df_dis.nprony > 0
    assert (df_dis["tau_i"] > 0).all()
    assert df_dis.domain == "freq"


@pytest.mark.parametrize("window", ["round", "exact", "min"])
def test_discretize_window_variants_time(time_master, window):
    df_master, _units = time_master
    df_dis = prony.discretize(df_master, window=window)
    assert df_dis.nprony > 0
    assert (df_dis["tau_i"] > 0).all()
    assert df_dis.domain == "time"


# ---------------------------------------------------------------------------
# fit with opt=True exercises the simultaneous (alpha_i, tau_i) minimization
# branches in both fit_time and fit_freq (including the split_x0 helper and
# the success/failure print messages).
# ---------------------------------------------------------------------------


def test_fit_freq_opt_true_runs(freq_master, capsys):
    df_master, _units = freq_master
    df_dis = prony.discretize(df_master, window="round")
    prony_fit, df_gmaxw = prony.fit(df_dis, df_master, opt=True)
    assert (prony_fit["df_terms"]["alpha_i"] >= 0).all()
    assert prony_fit["df_terms"]["alpha_i"].sum() <= 1.0 + 1e-9
    assert len(df_gmaxw) > 0
    # opt=True prints a "Convergence criterion" diagnostic
    assert "Convergence criterion" in capsys.readouterr().out


def test_fit_time_opt_true_runs(time_master, capsys):
    df_master, _units = time_master
    df_dis = prony.discretize(df_master, window="round")
    prony_fit, df_gmaxw = prony.fit(df_dis, df_master, opt=True)
    assert (prony_fit["df_terms"]["alpha_i"] >= 0).all()
    assert prony_fit["df_terms"]["alpha_i"].sum() <= 1.0 + 1e-9
    assert len(df_gmaxw) > 0
    assert "Convergence criterion" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# GMaxw_temp + plot_GMaxw_temp: temperature/rate sweep using a synthetic
# shift-factor dataset fitted with each supported shift function.
# ---------------------------------------------------------------------------


def _make_df_aT(RefT=-5.0):
    T = np.linspace(-40.0, 60.0, 21)
    log_aT = shift.WLF(T, RefT, 12.0, 80.0)
    return pd.DataFrame({"T": T, "log_aT": log_aT})


@pytest.mark.parametrize("shift_func", ["WLF", "D4", "D3", "D2", "D1"])
def test_GMaxw_temp_runs_for_each_shift_function(freq_master, shift_func):
    df_master, _units = freq_master
    df_dis = prony.discretize(df_master, window="round")
    _prony_fit, df_gmaxw = prony.fit(df_dis)

    df_aT = _make_df_aT(RefT=-5.0)
    df_WLF = shift.fit_WLF(-5.0, df_aT)
    df_C, _df_K = shift.fit_poly(df_aT)
    coeff = df_WLF if shift_func == "WLF" else df_C

    df_GMaxw_temp = prony.GMaxw_temp(shift_func, df_gmaxw, coeff, df_aT)
    assert "T" in df_GMaxw_temp.columns
    assert "f" in df_GMaxw_temp.columns
    assert df_GMaxw_temp.modul == "E"
    assert df_GMaxw_temp.domain == "freq"


def test_plot_GMaxw_temp(master_with_prony):
    """Smoke test ``plot_GMaxw_temp`` in both domains using a WLF fit on a
    synthetic shift-factor dataset."""
    df_master, units, _prony_fit, df_gmaxw = master_with_prony
    RefT = df_master.RefT
    df_aT = _make_df_aT(RefT=RefT)
    df_WLF = shift.fit_WLF(RefT, df_aT)
    df_GMaxw_temp = prony.GMaxw_temp("WLF", df_gmaxw, df_WLF, df_aT)

    fig = prony.plot_GMaxw_temp(df_GMaxw_temp, units)
    assert isinstance(fig, Figure)
    plt.close(fig)


# ---------------------------------------------------------------------------
# plot_param: bar plot of Prony series parameters
# ---------------------------------------------------------------------------


def test_plot_param(freq_master):
    """``plot_param`` accepts both default and custom labels."""
    df_master, _units = freq_master
    df_dis = prony.discretize(df_master, window="round")
    prony_fit, _df_gmaxw = prony.fit(df_dis)

    fig1 = prony.plot_param([prony_fit])
    assert isinstance(fig1, Figure)
    plt.close(fig1)

    fig2 = prony.plot_param([prony_fit, prony_fit], labels=["fit-a", "fit-b"])
    assert isinstance(fig2, Figure)
    plt.close(fig2)


# ---------------------------------------------------------------------------
# plot_dis / plot_GMaxw / plot_fit smoke tests across both domains
# ---------------------------------------------------------------------------


def test_plot_dis_and_GMaxw_and_fit(master_with_prony):
    """Smoke test plot_dis / plot_GMaxw / plot_fit in both domain branches."""
    df_master, units, _prony_fit, df_GMaxw = master_with_prony
    df_dis = prony.discretize(df_master, window="round")

    fig1 = prony.plot_dis(df_master, df_dis, units)
    assert isinstance(fig1, Figure)
    plt.close(fig1)

    fig2 = prony.plot_GMaxw(df_GMaxw, units)
    assert isinstance(fig2, Figure)
    plt.close(fig2)

    fig3 = prony.plot_fit(df_master, df_GMaxw, units)
    assert isinstance(fig3, Figure)
    plt.close(fig3)

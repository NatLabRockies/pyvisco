"""Tests for ``pyvisco.opt``: Prony-term minimization and its plots."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from pyvisco import opt


def test_nprony_returns_dict_and_optimum(master_with_prony):
    """``nprony`` must return a populated dict keyed by N, an integer ``N_opt``
    that maps into that dict, and a per-N residual ``DataFrame``."""
    df_master, _units, prony_fit, _df_gmaxw = master_with_prony
    dict_prony, N_opt, err = opt.nprony(df_master, prony_fit, window="min", opt=1.5)

    assert isinstance(dict_prony, dict)
    assert len(dict_prony) > 0
    assert N_opt in dict_prony
    # err is a DataFrame indexed by N with a single "res" column.
    assert isinstance(err, pd.DataFrame)
    assert "res" in err.columns
    assert err.modul == df_master.modul
    assert set(err.index) == set(dict_prony.keys())
    assert (err["res"] >= 0).all()


def test_plot_fit_and_residual(master_with_prony):
    """Smoke test ``opt.plot_fit`` and ``opt.plot_residual`` in both domains."""
    df_master, units, prony_fit, _df_gmaxw = master_with_prony
    dict_prony, N_opt, err = opt.nprony(df_master, prony_fit, window="min", opt=1.5)

    df_GMaxw, fig = opt.plot_fit(df_master, dict_prony, N_opt, units)
    assert isinstance(df_GMaxw, pd.DataFrame)
    modulus = "E_stor" if df_master.domain == "freq" else "E_relax"
    assert modulus in df_GMaxw.columns
    assert isinstance(fig, Figure)
    plt.close(fig)

    fig2 = opt.plot_residual(err)
    assert isinstance(fig2, Figure)
    plt.close(fig2)

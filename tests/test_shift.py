"""Tests for the WLF / polynomial shift-factor functions."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from pyvisco import shift


def test_wlf_zero_at_reference_temperature():
    """WLF must return log(a_T) = 0 at T == RefT."""
    assert shift.WLF(Temp=25.0, RefT=25.0, WLF_C1=17.44, WLF_C2=51.6) == 0.0


def test_wlf_known_value():
    """Reproduce a known WLF evaluation with classic 'universal' constants."""
    # log(a_T) = -C1*(T-Tref) / (C2 + (T-Tref))
    log_aT = shift.WLF(Temp=75.0, RefT=25.0, WLF_C1=17.44, WLF_C2=51.6)
    expected = -17.44 * 50.0 / (51.6 + 50.0)
    assert log_aT == expected


def test_fit_wlf_recovers_constants():
    """Generate synthetic shift factors from WLF and verify the fit recovers them."""
    RefT = 25.0
    C1_true, C2_true = 12.0, 80.0
    T = np.linspace(-20.0, 120.0, 25)
    log_aT = shift.WLF(T, RefT, C1_true, C2_true)

    df_aT = pd.DataFrame({"T": T, "log_aT": log_aT})
    df_fit = shift.fit_WLF(RefT, df_aT)

    assert df_fit.loc[0, "RefT"] == RefT
    np.testing.assert_allclose(df_fit.loc[0, "C1"], C1_true, rtol=1e-4)
    np.testing.assert_allclose(df_fit.loc[0, "C2"], C2_true, rtol=1e-4)


def test_polynomials_evaluate_correctly():
    """Each poly{N} should evaluate to the expected algebraic value."""
    x = 2.0
    assert shift.poly1(x, 1.0, 3.0) == 1.0 + 3.0 * x
    assert shift.poly2(x, 1.0, 0.0, 2.0) == 1.0 + 2.0 * x**2
    assert shift.poly3(x, 0.0, 1.0, 0.0, 0.5) == x + 0.5 * x**3
    assert shift.poly4(x, 1.0, 0.0, 0.0, 0.0, 0.25) == 1.0 + 0.25 * x**4


def test_fit_poly_returns_celsius_and_kelvin_frames():
    """fit_poly produces coefficient tables for both Celsius and Kelvin."""
    T = np.linspace(-20.0, 120.0, 25)
    # Quadratic-ish synthetic shift factors
    log_aT = -0.1 * (T - 25.0) + 0.002 * (T - 25.0) ** 2
    df_aT = pd.DataFrame({"T": T, "log_aT": log_aT})

    df_C, df_K = shift.fit_poly(df_aT)

    # Each frame has the four polynomial degrees as rows
    assert list(df_C.index) == ["D4", "D3", "D2", "D1"]
    assert list(df_K.index) == ["D4", "D3", "D2", "D1"]
    # And the coefficient columns
    assert df_C.columns.get_level_values(0).tolist() == ["C0", "C1", "C2", "C3", "C4"]


# ---------------------------------------------------------------------------
# Plot smoke test
# ---------------------------------------------------------------------------


def test_plot_returns_figure_and_dataframe():
    """Build synthetic shift factors, fit WLF + polynomials, then plot."""
    RefT = 25.0
    T = np.linspace(-20.0, 120.0, 25)
    log_aT = shift.WLF(T, RefT, 12.0, 80.0)
    df_aT = pd.DataFrame({"T": T, "log_aT": log_aT})

    df_WLF = shift.fit_WLF(RefT, df_aT)
    df_C, _df_K = shift.fit_poly(df_aT)

    fig, df_shift = shift.plot(df_aT, df_WLF, df_C)

    assert isinstance(fig, Figure)
    assert set(df_shift.columns) == {"T", "log_aT", "WLF", "Poly1", "Poly2", "Poly3", "Poly4"}
    assert len(df_shift) == len(T)
    plt.close(fig)

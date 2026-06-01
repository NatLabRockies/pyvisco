"""Tests for the WLF / polynomial shift-factor functions."""
from __future__ import annotations

import numpy as np
import pandas as pd

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

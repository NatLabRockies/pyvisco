"""Tests for the ANSYS verification helpers (``pyvisco.verify``)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pytest
from matplotlib.figure import Figure

from pyvisco import prony, verify

# ---------------------------------------------------------------------------
# load_prony_ANSYS
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("filename", "expected_nterms"),
    [("E1_WLF.USER_MPL", 30), ("E1_Poly.USER_MPL", 30)],
)
def test_load_prony_ANSYS_parses_attached_cards(tests_data_dir, filename, expected_nterms):
    """Both attached ANSYS .MPL cards must parse into the documented schema."""
    df = verify.load_prony_ANSYS(str(tests_data_dir / filename))
    assert list(df.columns) == ["tau_i", "alpha_i"]
    assert len(df) == expected_nterms
    assert df.index[0] == 1  # 1-indexed
    assert (df["tau_i"] > 0).all()
    assert (df["alpha_i"] > 0).all()
    # Header row in the attached cards:
    #   TBDATA,1,4.117658e-02,1.000000e-10,1.553623e-02
    # -> alpha_1 = 4.117658e-02, tau_1 = 1e-10
    assert df["alpha_i"].iloc[0] == pytest.approx(4.117658e-02)
    assert df["tau_i"].iloc[0] == pytest.approx(1.000000e-10)


def test_load_prony_ANSYS_bundled_verification_files():
    """The verification/ subdirectory ships .MPL files; ensure they still parse."""
    root = Path(__file__).resolve().parent.parent / "verification"
    for sub in ("freq_master", "freq_raw", "time_master"):
        df = verify.load_prony_ANSYS(str(root / sub / "prony_terms.MPL"))
        assert (df["tau_i"] > 0).all()
        assert (df["alpha_i"] > 0).all()
        assert df["alpha_i"].sum() <= 1.0 + 1e-9


def test_load_prony_ANSYS_raises_on_nterms_mismatch(tmp_path):
    """If TBDATA payload contains fewer pairs than declared, raise ValueError."""
    path = tmp_path / "bad_nterms.MPL"
    path.write_text(
        "TB,PRONY,_MAT,1,4,SHEAR\n"
        "TBDATA,1,0.1,1.0,0.2\n"  # 1 pair only (alpha, tau, alpha)
        "TBDATA,4,2.0\n"  # tau for second pair
    )
    with pytest.raises(ValueError, match="declared 4 Prony pairs"):
        verify.load_prony_ANSYS(str(path))


def test_load_prony_ANSYS_raises_on_alpha_tau_mismatch(tmp_path):
    """If parsing produces unequal alpha_i / tau_i counts, raise ValueError."""
    path = tmp_path / "bad_pairs.MPL"
    # 3-value payload yields 2 alpha but only 1 tau -> mismatch.
    path.write_text(
        "TB,PRONY,_MAT,1,2,SHEAR\n"
        "TBDATA,1,0.1,1.0,0.2\n"
    )
    with pytest.raises(ValueError, match="alpha_i values but"):
        verify.load_prony_ANSYS(str(path))


# ---------------------------------------------------------------------------
# prep_prony_ANSYS  (uses the ``master_with_prony`` fixture from conftest.py;
# only the frequency-domain instance is needed here -- the ANSYS schema is
# domain-agnostic.)
# ---------------------------------------------------------------------------


@pytest.fixture
def freq_prony_fit(freq_master):
    df_master, units = freq_master
    df_dis = prony.discretize(df_master, window="round")
    prony_fit, df_gmaxw = prony.fit(df_dis)
    return df_master, units, prony_fit, df_gmaxw


def test_prep_prony_ANSYS_defaults_to_python_E0(freq_prony_fit, tests_data_dir):
    _df_master, _units, prony_fit, _df_gmaxw = freq_prony_fit
    df_ansys = verify.load_prony_ANSYS(str(tests_data_dir / "E1_WLF.USER_MPL"))

    prony_ansys = verify.prep_prony_ANSYS(df_ansys, prony_fit)

    assert prony_ansys["E_0"] == prony_fit["E_0"]
    assert prony_ansys["f_min"] == prony_fit["f_min"]
    assert prony_ansys["f_max"] == prony_fit["f_max"]
    assert prony_ansys["modul"] == prony_fit["modul"]
    assert prony_ansys["label"] == "ANSYS"
    assert prony_ansys["df_terms"] is df_ansys


def test_prep_prony_ANSYS_respects_explicit_E0(freq_prony_fit, tests_data_dir):
    _df_master, _units, prony_fit, _df_gmaxw = freq_prony_fit
    df_ansys = verify.load_prony_ANSYS(str(tests_data_dir / "E1_WLF.USER_MPL"))

    override = 9.1158e9  # the EX from the attached card
    prony_ansys = verify.prep_prony_ANSYS(df_ansys, prony_fit, E_0=override)

    assert prony_ansys["E_0"] == override
    # f_min / f_max still come from the Python fit
    assert prony_ansys["f_min"] == prony_fit["f_min"]
    assert prony_ansys["f_max"] == prony_fit["f_max"]


# ---------------------------------------------------------------------------
# plot_fit_ANSYS (smoke test for both domains via ``master_with_prony``)
# ---------------------------------------------------------------------------


def test_plot_fit_ANSYS(master_with_prony, tests_data_dir):
    df_master, units, prony_fit, df_gmaxw = master_with_prony
    df_ansys = verify.load_prony_ANSYS(str(tests_data_dir / "E1_WLF.USER_MPL"))
    prony_ansys = verify.prep_prony_ANSYS(df_ansys, prony_fit)
    # calc_GMaxw needs ``decades`` separately (matches usage in the
    # verification notebooks: ``calc_GMaxw(**prony_ANSYS, decades=nprony)``).
    df_gmaxw_ansys = prony.calc_GMaxw(**prony_ansys, decades=prony_fit["decades"])
    df_gmaxw_ansys.domain = df_master.domain

    fig = verify.plot_fit_ANSYS(df_master, df_gmaxw, df_gmaxw_ansys, units)
    assert isinstance(fig, Figure)
    plt.close(fig)

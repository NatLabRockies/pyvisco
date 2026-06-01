"""Round-trip tests for the Prony series fitting pipeline."""

from __future__ import annotations

import numpy as np

from pyvisco import load, master, prony


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


def test_time_domain_pipeline_roundtrip(examples_dir):
    """End-to-end fit on the bundled time-domain master curve.

    Loads the example master curve, discretizes relaxation times, fits a Prony
    series, reconstructs the Generalized Maxwell response, and asserts the
    reconstruction matches the input data to within a tight tolerance.
    """
    path = examples_dir / "time_user_master.csv"
    data = load.file(str(path))
    df_master, units = load.user_master(data, domain="time", RefT=25.0, modul="E")

    # Smooth (creates the *_filt column required by the fit)
    df_master = master.smooth(df_master, win=1)

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

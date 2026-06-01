"""Tutorial script: frequency-domain raw Eplexor measurement.

Mirrors verification/verify_freq_raw.ipynb but runs as a headless script.
Figures are written to tutorials/_figures/.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import pyvisco as visco
from pyvisco import styles

SAMPLE_DATA = Path(__file__).resolve().parent.parent / "sample_data"
FIG_DIR = Path(__file__).resolve().parent / "_figures"
FIG_DIR.mkdir(exist_ok=True)


def save(fig, name: str) -> None:
    fig.savefig(FIG_DIR / f"freq_raw_{name}.png", dpi=120, bbox_inches="tight")


def main() -> None:
    styles.format_fig()

    # Load Eplexor raw measurement
    modul = "E"
    RefT = -5  # must match a measurement set temperature

    epl_raw = visco.load.file(SAMPLE_DATA / "freq_Eplexor_raw.xls")
    df_raw, arr_RefT, units = visco.load.Eplexor_raw(epl_raw, modul)

    # Fit shift factors and build master curve
    df_aT, dshift = visco.master.get_aT(df_raw, RefT)
    df_master = visco.master.get_curve(df_raw, df_aT, RefT)
    fig_shift_master, _ = visco.master.plot_shift(df_raw, df_master, units)
    save(fig_shift_master, "01_shift_master")

    # Shift functions (WLF + polynomial)
    df_WLF = visco.shift.fit_WLF(df_master.RefT, df_aT)
    df_poly_C, df_poly_K = visco.shift.fit_poly(df_aT)
    fig_shift, _ = visco.shift.plot(df_aT, df_WLF, df_poly_C)
    save(fig_shift, "02_shift_functions")

    # Smooth + discretize
    df_master = visco.master.smooth(df_master, win=5)
    fig_smooth = visco.master.plot_smooth(df_master, units)
    save(fig_smooth, "03_smooth")

    df_dis = visco.prony.discretize(df_master)
    fig_dis = visco.prony.plot_dis(df_master, df_dis, units)
    save(fig_dis, "04_discretize")

    # Prony fit
    prony, df_GMaxw = visco.prony.fit(df_dis)
    fig_fit = visco.prony.plot_fit(df_master, df_GMaxw, units)
    save(fig_fit, "05_prony_fit")

    fig_GMaxw = visco.prony.plot_GMaxw(df_GMaxw, units)
    save(fig_GMaxw, "06_GMaxw")

    # Optional: optimize number of Prony terms
    dict_prony, N_opt, N_opt_err = visco.opt.nprony(df_master, prony, window="min")
    _, fig_opt = visco.opt.plot_fit(df_master, dict_prony, N_opt, units)
    save(fig_opt, "07_opt_fit")
    fig_res = visco.opt.plot_residual(N_opt_err)
    save(fig_res, "08_opt_residual")

    fig_param = visco.prony.plot_param(
        [prony, dict_prony[N_opt]], ["initial", "optimized"]
    )
    save(fig_param, "09_param")

    print(f"Done. Figures written to {FIG_DIR}")
    print(f"  initial Prony terms : {prony['df_terms'].shape[0]}")
    print(f"  optimized Prony terms: {N_opt}")


if __name__ == "__main__":
    main()

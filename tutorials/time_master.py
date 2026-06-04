"""Tutorial script: user-provided master curve in the time domain.

Mirrors verification/verify_time_master.ipynb but runs as a headless script.
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
    fig.savefig(FIG_DIR / f"time_master_{name}.png", dpi=120, bbox_inches="tight")


def main() -> None:
    styles.format_fig()

    RefT = -5
    domain = "time"
    modul = "E"

    data = visco.load.file(SAMPLE_DATA / "time_user_master.csv")
    df_master, units = visco.load.user_master(data, domain, RefT, modul)

    # Smooth + discretize
    df_master = visco.master.smooth(df_master, win=1)
    fig_smooth = visco.master.plot_smooth(df_master, units)
    save(fig_smooth, "01_smooth")

    df_dis = visco.prony.discretize(df_master)
    fig_dis = visco.prony.plot_dis(df_master, df_dis, units)
    save(fig_dis, "02_discretize")

    # Prony fit (time domain requires df_master)
    prony, df_GMaxw = visco.prony.fit(df_dis, df_master)
    fig_fit = visco.prony.plot_fit(df_master, df_GMaxw, units)
    save(fig_fit, "03_prony_fit")

    fig_GMaxw = visco.prony.plot_GMaxw(df_GMaxw, units)
    save(fig_GMaxw, "04_GMaxw")

    # Optional: optimize number of Prony terms
    dict_prony, N_opt, N_opt_err = visco.opt.nprony(df_master, prony, window="min")
    _, fig_opt = visco.opt.plot_fit(df_master, dict_prony, N_opt, units)
    save(fig_opt, "05_opt_fit")
    fig_res = visco.opt.plot_residual(N_opt_err)
    save(fig_res, "06_opt_residual")

    fig_param = visco.prony.plot_param(
        [prony, dict_prony[N_opt]], ["initial", "optimized"]
    )
    save(fig_param, "07_param")

    print(f"Done. Figures written to {FIG_DIR}")
    print(f"  initial Prony terms : {prony['df_terms'].shape[0]}")
    print(f"  optimized Prony terms: {N_opt}")


if __name__ == "__main__":
    main()

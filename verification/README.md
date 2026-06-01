# Verification

Cross-checks of pyvisco's Prony-series fits against [ANSYS APDL 2021 R1].
Each notebook loads measurement data, runs the full pyvisco pipeline, then
compares the resulting Generalized Maxwell parameters with the reference
`prony_terms.MPL` produced by APDL on the same input.

| Notebook | Input | Reference |
|---|---|---|
| [`verify_freq_raw.ipynb`](verify_freq_raw.ipynb) | Eplexor raw frequency-domain measurement | [`freq_raw/prony_terms.MPL`](freq_raw/prony_terms.MPL) |
| [`verify_freq_master.ipynb`](verify_freq_master.ipynb) | User-provided frequency-domain master curve + shift factors | [`freq_master/prony_terms.MPL`](freq_master/prony_terms.MPL) |
| [`verify_time_master.ipynb`](verify_time_master.ipynb) | User-provided time-domain master curve | [`time_master/prony_terms.MPL`](time_master/prony_terms.MPL) |

The accompanying `job_prony_fit.mac` files in each subfolder are the APDL
macros used to generate the reference fits.

## CI

These notebooks are executed end-to-end on every push by
[`.github/workflows/notebooks.yml`](../.github/workflows/notebooks.yml)
via `pytest --nbval-lax`. Output comparison is intentionally disabled:
the notebooks use `%matplotlib ipympl`, whose Canvas widget HTML repr is
not stable across platforms. The numeric comparison against the APDL
reference happens inside `visco.verify.plot_fit_ANSYS`, so a successful
run already confirms agreement with the reference fit.

## Running locally

```bash
pip install -e ".[test]"
pytest --nbval-lax verification/
```

[ANSYS APDL 2021 R1]: https://www.ansys.com/products/ansys-workbench

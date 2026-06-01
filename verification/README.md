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

These notebooks are executed and their outputs compared on every push by
[`.github/workflows/notebooks.yml`](../.github/workflows/notebooks.yml) using
`pytest --nbval` together with [`nbval_sanitize.cfg`](nbval_sanitize.cfg),
which masks numeric drift (floating-point tails, widget `model_id`s, memory
addresses, figure-size repr) so genuine regressions stand out.

## Running locally

```bash
pip install -e ".[test]"
pytest --nbval --sanitize-with verification/nbval_sanitize.cfg verification/
```

[ANSYS APDL 2021 R1]: https://www.ansys.com/products/ansys-workbench

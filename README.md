# pyvisco

[![CI](https://github.com/NatLabRockies/pyvisco/actions/workflows/ci.yml/badge.svg)](https://github.com/NatLabRockies/pyvisco/actions/workflows/ci.yml)
[![Notebooks](https://github.com/NatLabRockies/pyvisco/actions/workflows/notebooks.yml/badge.svg)](https://github.com/NatLabRockies/pyvisco/actions/workflows/notebooks.yml)
[![Hugging Face Space](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Space-blue)](https://huggingface.co/spaces/mspringer-nlr/pyvisco-voila)
[![Documentation Status](https://readthedocs.org/projects/pyvisco/badge/?version=latest)](https://pyvisco.readthedocs.io/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/pyvisco.svg)](https://pypi.org/project/pyvisco/)
[![Python](https://img.shields.io/pypi/pyversions/pyvisco.svg)](https://pypi.org/project/pyvisco/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6384954.svg)](https://doi.org/10.5281/zenodo.6384954)

Pyvisco is a Python library that supports the identification of Prony series parameters for Generalized Maxwell models describing linear viscoelastic materials.

## Overview

The mechanical response of linear viscoelastic materials is often described with Generalized Maxwell models. The necessary material model parameters are typically identified by fitting a Prony series to the experimental measurement data in either the frequency-domain (via Dynamic Mechanical Thermal Analysis) or time-domain (via relaxation measurements). Pyvisco performs the necessary data processing of the experimental measurements, mathematical operations, and curve-fitting routines to identify the Prony series parameters. The experimental data can be provided as raw measurement sets at different temperatures or as pre-processed master curves.

* If raw measurement data are provided, the time-temperature superposition principle is applied to create a master curve and obtain the shift functions prior to the Prony series parameters identification.

* If master curves are provided, the shift procedure can be skipped, and the Prony series parameters identified directly.

An optional minimization routine is provided to reduce the number of Prony elements. This routine is helpful for Finite Element simulations where reducing the computational complexity of the linear viscoelastic material models can shorten the simulation time.

## Installation

```bash
pip install pyvisco
```

Requires Python 3.11 or newer.

## Example data

Bundled example input files live under [`sample_data/`](sample_data/) and
are also published as a downloadable archive on every GitHub release:
[`pyvisco-examples.zip`](https://github.com/NatLabRockies/pyvisco/releases/latest/download/pyvisco-examples.zip).
These files can be loaded directly into the web app, the tutorial
notebook, or any of the standalone scripts described below.

## Usage

There are three ways to use pyvisco:

1. **Interactive web app (no install required).** The `LinViscoFit.ipynb` notebook provides a graphical interface (upload data → fit → download Prony series) and is hosted as a Voila application on Hugging Face Spaces:

   [![Hugging Face Space](https://img.shields.io/badge/%F0%9F%A4%97%20Open%20app-Hugging%20Face%20Space-blue)](https://huggingface.co/spaces/mspringer-nlr/pyvisco-voila)

   The Space tracks the `main` branch and rebuilds automatically. The
   first request after a period of inactivity may take ~30s while the
   container wakes up. The same app can also be run locally with
   `voila LinViscoFit.ipynb` after a `pip install pyvisco`.

2. **Tutorial notebook & scripts.** The [`tutorials/`](tutorials/) folder contains a non-interactive walkthrough notebook (`tutorial.ipynb`) and three standalone Python scripts (`freq_master.py`, `freq_raw.py`, `time_master.py`) mirroring the verification scenarios — suitable for headless / CI / batch use.

3. **As a library.** Import `pyvisco` and call the modules directly. See the [API documentation](https://pyvisco.readthedocs.io/en/latest/) for details.

## Verification

The Python implementation is verified against the curve-fitting routine of the commercial package ANSYS APDL 2021 R1. The notebooks and reference material cards live in the [`verification/`](verification/) folder and are executed end-to-end on every push.

## Citation

If you use pyvisco in your published work, please cite it along with the version number and the specific DOI for that version on Zenodo: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6384954.svg)](https://doi.org/10.5281/zenodo.6384954).

### APA

```
Springer, Martin (2022). PYVISCO: A Python library for identifying Prony series parameters of linear viscoelastic materials (Version {insert version}) [Computer software]. doi:{insert DOI}
```

### BibTeX

```bibtex
@software{Springer_pyvisco_2022,
  author  = {Springer, Martin},
  doi     = {insert DOI},
  title   = {{PYVISCO: A Python library for identifying Prony series parameters of linear viscoelastic materials}},
  url     = {https://github.com/NatLabRockies/pyvisco},
  version = {insert version},
  year    = {2022}
}
```

## Contributing

Bug reports, questions, and pull requests are welcome. See
[CONTRIBUTING.md](CONTRIBUTING.md) for how to report issues, ask for
support, set up a development environment, and submit changes.

## License

Released under the [BSD 3-Clause](LICENSE) license.

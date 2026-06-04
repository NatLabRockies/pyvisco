# Contributing to pyvisco

Thanks for your interest in improving `pyvisco`. This document explains how
to report issues, ask for help, and contribute code or documentation.
Participation in this project is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting issues

Please open a [GitHub Issue](https://github.com/NatLabRockies/pyvisco/issues)
for bug reports, regressions, or unexpected numerical results. A useful
report includes:

- the `pyvisco` version (`python -c "import pyvisco; print(pyvisco.__version__)"`)
  and Python version,
- the operating system,
- a minimal, self-contained example that reproduces the problem
  (the files under [`sample_data/`](sample_data/) are a good starting point),
- the full traceback or, for numerical issues, the expected vs. observed
  output.

Before opening a new issue, please search existing issues (both open and
closed) to avoid duplicates.

## Asking for help

For usage questions that are not bug reports (e.g., "how do I fit a master
curve from format X?", "which shift function should I use?"):

- check the [documentation on Read the Docs](https://pyvisco.readthedocs.io/),
  the tutorial notebook and scripts under [`tutorials/`](tutorials/), and the
  verification notebooks under [`verification/`](verification/);
- if the question is still unanswered, open a GitHub Issue with the
  `question` label.

There is no separate mailing list or chat channel; GitHub Issues is the
single support channel.

## Contributing code or documentation

1. **Fork** the repository and create a feature branch from `main`.
2. **Install** the development environment:
   ```bash
   pip install -e ".[dev]"
   ```
   This installs the test dependencies (`pytest`, `pytest-cov`, `nbval`),
   the documentation dependencies, and linting tools (`ruff`, `pre-commit`).
3. **Make your change.** Keep changes focused; prefer separate PRs for
   unrelated fixes.
4. **Run the tests** locally:
   ```bash
   pytest
   ```
   For changes that affect the notebooks, also run:
   ```bash
   pytest --nbval-lax LinViscoFit.ipynb tutorials/tutorial.ipynb \
       verification/verify_freq_master.ipynb \
       verification/verify_freq_raw.ipynb \
       verification/verify_time_master.ipynb
   ```
5. **Update documentation and the changelog** under
   [`docs/changelog/`](docs/changelog/) when your change is user-visible.
6. **Open a Pull Request** against `main`. The CI workflows (`CI` and
   `Notebooks`) will run automatically; please make sure they pass.

## Verification against ANSYS APDL

`pyvisco` is validated against the curve-fitting routine of ANSYS APDL
2021 R1 using the reference cases under [`verification/`](verification/).
If your change touches the fitting routines (`pyvisco/prony.py`,
`pyvisco/master.py`, `pyvisco/shift.py`, `pyvisco/opt.py`), please re-run
the verification notebooks and confirm the comparison plots still match the
APDL reference.

## License

By contributing, you agree that your contributions will be licensed under
the same [BSD 3-Clause license](LICENSE) as the rest of the project.

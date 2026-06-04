---
title: 'pyvisco: A Python library for identifying Prony series parameters of linear viscoelastic materials'
tags:
  - Python
  - viscoelasticity
  - material modeling
  - Prony series
  - Generalized Maxwell model
  - curve fitting
  - dynamic mechanical analysis
  - time-temperature superposition
  - finite element analysis
authors:
  - name: Martin Springer
    orcid: 0000-0001-6803-108X
    corresponding: true
    affiliation: 1
affiliations:
  - name: National Laboratory of the Rockies, United States
    index: 1
    ror: "036266993"
date: 2 June 2026
bibliography: paper.bib
---

# Summary

Polymeric materials commonly used in engineering applications, such as the
encapsulants and backsheets in photovoltaic modules, adhesives in structural
joints, and rubbers in seals and dampers, exhibit time- and
temperature-dependent mechanical behavior. The theory of linear viscoelasticity
provides a framework to describe this behavior, and the Generalized Maxwell
model represented through a Prony series is widely adopted in commercial
finite element analysis (FEA) software to simulate viscoelastic response of
thermorheologically simple materials under
mechanical and thermal loads. Identifying the Prony series parameters from
experimental measurements is, however, a non-trivial multi-step process that
involves data conditioning, time–temperature superposition (TTSP), shift
function fitting, and constrained non-linear least-squares optimization.

`pyvisco` is an open-source Python library that automates this workflow.
Given either raw isothermal measurements at multiple temperatures (from
dynamic mechanical thermal analysis or relaxation experiments) or a
pre-assembled master curve, the library constructs the master curve via TTSP,
fits Williams–Landel–Ferry (WLF) and polynomial shift functions, and
identifies the relaxation times $\tau_i$ and moduli $E_i$ (or shear moduli
$G_i$) of a Prony series compatible with the Generalized Maxwell model. An
optional minimization routine produces a reduced-term Prony series suitable
for computationally efficient FEA simulations. The library is accessible through
a programmatic application programming interface (API) and through a
Jupyter-based graphical user interface (`LinViscoFit.ipynb`) that runs without
local installation as a Voila application on Hugging Face Spaces. Library outputs
are verified against the curve-fitting routine of ANSYS APDL
2021 R1 (ANSYS Inc., Canonsburg, Pennsylvania) using bundled reference cases.

# Statement of need

Linear viscoelastic material models are routinely required by researchers
and engineers working with polymers in structural, thermal, and reliability
analyses. The underlying mathematical framework is well established and
combines the Boltzmann superposition integral, the Generalized Maxwell
model, time--frequency interconversion via Fourier transformation, and
TTSP [@brinson2015polymer; @ferry1980viscoelastic;
@park1999methods; @roylance2001engineering; @williams1955temperature].
This framework forms the basis of the characterization workflow described
by @springer2020fracture, on which `pyvisco` is built. However, translating raw
experimental data into a Prony series suitable for FEA is
tedious and error-prone. The process typically requires:

- shifting isothermal measurement sets in the frequency or time domain to
  form a master curve at a reference temperature;
- fitting a shift function (e.g., WLF [@williams1955temperature],
  Arrhenius, or low-degree polynomial) to parameterize the temperature
  dependence;
- selecting an appropriate number and distribution of Prony terms;
- solving a bound-constrained least-squares problem to identify $\tau_i$
  and $E_i$ while enforcing $E_\infty \geq 0$ and $\sum \alpha_i \leq 1$;
- optionally reducing the number of Prony terms to keep FEA simulations
  tractable.

Many researchers implement this pipeline ad hoc in spreadsheets or short
scripts. Furthermore, commercial dynamic mechanical thermal analysis (DMTA) software
(e.g., Netzsch GABO Eplexor, TA Instruments TRIOS) typically allows only
a subset of these steps and offers
limited interoperability with FEA pre-processors. `pyvisco` was designed to
fill this gap with a reproducible, open-source workflow that:

1. accepts both raw and pre-shifted master-curve inputs in CSV or Eplexor
   Excel format;
2. produces Prony series output cards directly usable in commercial FEA codes;
3. is accessible to non-programmers through a browser-based notebook
   interface (powered by `ipywidgets`) without local installation; and
4. is verified against ANSYS APDL on a reference benchmark set kept in the
   repository.

The library targets researchers characterizing polymeric materials (e.g., photovoltaic (PV)
encapsulants, adhesives, elastomers, hydrogels) and engineers preparing
material cards for viscoelastic FEA simulations.

# State of the field

A number of tools touch parts of the viscoelastic characterization workflow:

- **Commercial DMTA software** (Netzsch GABO Eplexor, TA Instruments TRIOS,
  Anton Paar RheoCompass) can construct master curves and fit shift
  functions, but Prony series export and reduced-term optimization for FEA
  are limited or absent, and licensing restricts reproducibility.
- **`pyRheo`** [@miranda2024pyrheo] focuses on rheological model fitting
  (fractional and integer-order constitutive models) but does not target
  Prony-series identification for the Generalized Maxwell model used in FEA,
  nor does it integrate the full TTSP pipeline.
- **`RepTate`** [@boudara2020reptate] is an open-source rheology data
  analysis suite with a Qt GUI; while powerful for rheological model
  selection, it is primarily a desktop application and does not export
  Prony-series cards specifically tuned for finite element use.
- **Bespoke MATLAB/Python scripts** are common in the literature
  [@barrientos2019optimal; @park1999methods] but are typically not packaged,
  tested, or maintained beyond a single publication.

`pyvisco` was built as a focused, reusable package because none of the above
combine: (a) a full raw-data-to-Prony-series workflow in a single tool, (b)
an optimization routine that yields a reduced-term Prony series suitable for
FEA, (c) verification against a commercial FEA software's own fitting routine,
and (d) a zero-install browser interface that lowers the barrier for
non-Python users working in materials labs. Where alternatives are well suited to
their target use cases, `pyvisco` complements them by closing the loop
between DMTA measurements and FEA input decks.

# Software design

`pyvisco` is organized as a small set of single-purpose modules
(`load`, `master`, `shift`, `prony`, `opt`, `out`, `verify`, `styles`,
`inter`) that each expose pure functions operating on `pandas.DataFrame`
inputs. This functional, dataframe-centric design was chosen so that:

- each step (loading, master-curve assembly, shift-function fitting,
  Prony fitting, optimization, output) can be invoked, inspected, and unit
  tested in isolation;
- intermediate states are first-class data artifacts that can be cached,
  exported, or visualized without re-running upstream computations; and
- the user interface layer (`inter.py`, an `ipywidgets`-based controller)
  is a thin orchestration layer with no domain logic of its own.

The Prony fit is formulated as a bound-constrained non-linear least-squares
problem solved with SciPy's L-BFGS-B implementation [@virtanen2020scipy],
following the formulation of @barrientos2019optimal and the
interconversion methodology of @park1999methods. Time-domain to
frequency-domain conversion of relaxation data uses the Fourier
transformation summarized in @springer2020fracture. Master curves are
optionally smoothed using a Savitzky--Golay filter [@savitzky1964smoothing]
before Prony-series fitting to suppress measurement noise without
broadening the relaxation spectrum. The reduced-term optimization routine
progressively removes Prony terms and refits, using the ratio of residuals
($R^2_{\mathrm{opt}} \approx 1.5\,R^2_0$) as a default stopping heuristic
that the user can override. Numerical routines build on `numpy`
[@harris2020array], `scipy` [@virtanen2020scipy], `pandas`
[@mckinney2010data], and `matplotlib` [@hunter2007matplotlib]; the graphical
user interface (GUI) is served by Voila as a Docker-based Hugging Face Space.

Outputs include the fitted Prony parameters as CSV, plots in PNG, and a
single ZIP archive bundling all results for downstream FEA use. The
`verification/` directory contains end-to-end notebooks comparing `pyvisco`
fits against ANSYS APDL 2021 R1 reference cases; these notebooks are
executed on every push via GitHub Actions to guard against regressions.

# Research impact statement

`pyvisco` originated to support viscoelastic characterization of PV
module encapsulants and interconnect adhesives, as part of the
reliability and durability research described by @springer2020fracture.
Since its initial public release in 2022 the package has been published on
PyPI, archived on Zenodo with a DOI per release [@springer2022pyvisco],
indexed by Read the Docs,
and developed openly on GitHub with continuous integration, an issue
tracker, a tagged release history, and a public changelog spanning the v1.x
and v2.x series.

The v2.0 release re-organized the codebase into the modular layout described
above, added a verified test suite, modernized the packaging (PEP 621
`pyproject.toml`, Python ≥ 3.11), and introduced standalone tutorial scripts
in addition to the interactive notebook so the library can be used in
headless and continuous-integration contexts.

Beyond its originating use case, `pyvisco` has been adopted by independent
research groups across a range of polymer-mechanics domains. To date the
software has been used in at least eight peer-reviewed publications and
technical reports, including: fractional-calculus modeling of methylcellulose
aqueous systems [@mirandavaldez2024methylcellulose]; finite-strain
viscoelastic-damage modeling of solid propellants [@gouhier2024solid];
characterization and modeling of waterborne epoxy varnish coatings for
steel/epoxy laminates in electric machines [@tiefenthaler2025steel];
structural-dynamic characterization of polymeric foams via time–temperature
superposition [@lebarbenchon2025foam]; fatigue testing of bitumen binders
using column specimens [@shine2023bitumen]; nano-indentation DMTA
characterization of polymeric materials in microelectronic packaging
[@lin2024nidmta]; viscoelastic characterization of polymer films
[@lin2025polymerfilms]; and biomechanical modeling of handball-induced head
injuries [@johansson2024handball]. These applications span food science,
aerospace propellants, electric-machine manufacturing, cellular polymers,
road-pavement engineering, microelectronics packaging, and sports
biomechanics, demonstrating that the workflow generalizes well beyond its
original PV context.

By providing a reproducible, open, and FEA-oriented Prony identification
workflow, `pyvisco` complements existing rheology packages and lowers the
barrier for materials researchers to share viscoelastic material cards in a
form directly usable by the wider engineering community.

# AI usage disclosure

Generative AI tools were used during the preparation of the v2.x release and
of this manuscript:

- **Tools/models used:** GitHub Copilot in Visual Studio Code (Claude Opus
  4.7 and GPT-class models accessed through Copilot Chat), used during
  development between 2024 and 2026.
- **Where used:** (a) refactoring of the v1.x codebase into the modular
  layout, including renaming and reorganization of functions; (b) drafting
  and updating user-facing documentation (`README.md`, the changelog under
  `docs/changelog/`, docstrings, tutorial scripts); (c) drafting unit-test
  scaffolding under `tests/`; (d) initial drafting of this `paper.md`.
- **Where not used:** the core numerical formulation of the Prony fit,
  shift-function fits, and time-temperature superposition algorithms
  predate the use of AI assistance and were authored by the human author;
  the verification notebooks against ANSYS APDL and their reference data
  were authored manually.
- **Verification:** All AI-assisted code was reviewed by the author before
  commit, executed locally, and validated by the existing test suite and the
  end-to-end verification notebooks comparing `pyvisco` outputs against
  ANSYS APDL. AI-assisted prose was reviewed and edited by the author for
  accuracy. The author takes full responsibility for the correctness,
  originality, and licensing of all materials in this submission.

# Acknowledgements

The author thanks colleagues for early feedback on the workflow, and the
maintainers of `numpy`, `scipy`, `pandas`, `matplotlib`, and `ipywidgets`
on which `pyvisco` builds.

This work was authored by the National Laboratory of the Rockies for the
U.S. Department of Energy (DOE), operated under Contract
No. DE-AC36-08GO28308. Funding was provided as part of the Durable Module
Materials Consortium 2 (DuraMAT 2), funded by the U.S. Department of
Energy Office of Critical Minerals and Energy Innovation Integrated
Energy Systems Office, agreement number 38259. The views expressed in
the article do not necessarily represent the views of the DOE or the
U.S. Government. The U.S. Government retains and the publisher, by
accepting the article for publication, acknowledges that the
U.S. Government retains a nonexclusive, paid-up, irrevocable, worldwide
license to publish or reproduce the published form of this work, or
allow others to do so, for U.S. Government purposes.

# References

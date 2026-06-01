#!/usr/bin/env python3

"""Collection of submodules to identify Prony series parameters of linear
viscoelastic materials from measurements in either the time (relaxation tests)
or frequency domain (DMTA).
"""

from importlib.metadata import PackageNotFoundError, version

from . import load, master, opt, out, prony, shift, verify

__all__ = ["load", "master", "opt", "out", "prony", "shift", "verify", "__version__"]

try:
    __version__ = version("pyvisco")
except PackageNotFoundError:  # package not installed
    __version__ = "0.0.0+unknown"

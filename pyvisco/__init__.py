#!/usr/bin/env python3

"""Collection of submodules to identify Prony series parameters of linear 
viscoelastic materials from measurements in either the time (relaxation tests) 
or frequency domain (DMTA).
"""

from importlib.metadata import PackageNotFoundError, version

from . import load
from . import shift
from . import master
from . import prony
from . import opt
from . import verify
from . import out

try:
    __version__ = version("pyvisco")
except PackageNotFoundError:  # package not installed
    __version__ = "0.0.0+unknown"


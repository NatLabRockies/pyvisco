"""Shared pytest fixtures."""
from __future__ import annotations

from pathlib import Path

import pytest

# Use a non-interactive matplotlib backend so plotting code never opens a window
import matplotlib

matplotlib.use("Agg")


@pytest.fixture(scope="session")
def examples_dir() -> Path:
    """Path to the bundled examples directory."""
    return Path(__file__).resolve().parent.parent / "examples"

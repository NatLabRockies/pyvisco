"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

# Use a non-interactive matplotlib backend so plotting code never opens a window
import matplotlib
import pytest

matplotlib.use("Agg")


@pytest.fixture(scope="session")
def sample_data_dir() -> Path:
    """Path to the bundled sample-data directory."""
    return Path(__file__).resolve().parent.parent / "sample_data"

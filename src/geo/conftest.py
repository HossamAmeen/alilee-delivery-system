"""App-level pytest config for the geo app.

This file is intentionally minimal. pytest will automatically make fixtures from
the project-level `src/conftest.py` available to tests in this package.

Add app-specific fixtures here when needed.
"""

import pytest


__all__ = ["pytest"]

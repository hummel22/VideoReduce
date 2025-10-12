"""Pytest configuration for backend tests."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repository root is on sys.path so `import backend` works when tests
# are executed without installing the package.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

"""Unit tests configuration.

Ensures the app package is importable and disables Redis connections,
so unit tests run without external services.
"""

import os
import sys
from pathlib import Path

# Make `backend` importable so `import app` works
_BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Disable real Redis connections for unit tests
os.environ.setdefault("DISABLE_REDIS", "1")


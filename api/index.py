from __future__ import annotations

import sys
from pathlib import Path

# Ensure the backend package folder is importable in Vercel's serverless runtime.
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402

"""Compatibility entry point for the single KHUTA FastAPI application.

The simulated tap API and future RFID requests are served by the same backend
implementation in ``backend/app/api.py``.
"""
from pathlib import Path
import sys

BACKEND_DIR=Path(__file__).resolve().parent/'backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0,str(BACKEND_DIR))

from app.api import app  # noqa: E402,F401

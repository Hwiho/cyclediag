"""Run archived cyclediag CLI without restoring files to the package root."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from cyclediag.archive.cli.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())

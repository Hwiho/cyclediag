"""Extract cycle indicators (rest V, R, SoHQ…) → Excel for offline check.

Usage:
  python run_export_cycle_indicators.py --input path/to/cell_raw.csv
  python run_export_cycle_indicators.py --input path/to/folder --out-dir C:/tmp
"""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).resolve().parent / "cyclediag" / "tools" / "export_cycle_indicators.py"),
        run_name="__main__",
    )

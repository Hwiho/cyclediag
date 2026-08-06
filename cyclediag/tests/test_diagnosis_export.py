"""Tests for unified diagnosis export bundle."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from cyclediag.analysis.indicator_screen import screen_indicators
from cyclediag.features.diagnosis_export import (
    export_diagnosis_from_features,
    save_diagnosis_pngs,
)
from cyclediag.tests.test_indicator_screen import _synthetic_features


def test_save_diagnosis_pngs(tmp_path: Path):
    df = _synthetic_features(40, "cell_A")
    screened = screen_indicators(df)
    pngs = save_diagnosis_pngs(
        df, tmp_path, stem="test", screened=screened, per_cell=False,
    )
    assert len(pngs) >= 2
    for p in pngs:
        assert p.is_file()
        assert p.stat().st_size > 1000


def test_export_diagnosis_from_features(tmp_path: Path):
    df = _synthetic_features(40, "cell_A")
    result = export_diagnosis_from_features(df, tmp_path, stem="cellA")
    assert result.out_csv is not None and result.out_csv.is_file()
    assert result.out_screen_csv is not None and result.out_screen_csv.is_file()
    assert result.out_xlsx is not None and result.out_xlsx.is_file()
    assert len(result.out_pngs) >= 2

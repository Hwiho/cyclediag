from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.origin_ppt.build_slides import all_slides
from cyclediag.origin_ppt.data import load_arm_tables, load_tagged, overlay_metric_series, series_for_cells


class OriginPptDataTests(unittest.TestCase):
    def test_arm_soc0_series(self) -> None:
        tables = load_arm_tables()
        self.assertIn("M01Ch022", tables)
        series = series_for_cells(tables, ("M01Ch022", "M01Ch024"), xcol="tagged_cycle", ycol="dchg_dVdQ_SOC0")
        self.assertEqual(len(series), 2)
        self.assertGreater(len(series[0]["x"]), 50)
        self.assertEqual(len(series[0]["x"]), len(series[0]["y"]))

    def test_overlay_columns(self) -> None:
        tagged = load_tagged()
        df = tagged["SJ900"]
        series = overlay_metric_series(df, ("M01Ch022", "M01Ch024", "M01Ch025"), "dchg_dVdQ_SOC0")
        self.assertEqual({row["label"] for row in series}, {"M01Ch022", "M01Ch024", "M01Ch025"})

    def test_slide_specs_without_profiles(self) -> None:
        slides = all_slides(load_arm_tables(), load_tagged(), refresh_profiles=False, skip_profiles=True)
        kinds = [s["kind"] for s in slides]
        self.assertEqual(kinds[0], "cover")
        self.assertIn("graphs", kinds)
        self.assertEqual(kinds[-1], "summary")
        names = []
        for spec in slides:
            for graph in spec.get("graphs") or []:
                names.append(graph["ole_name"])
                self.assertTrue(graph["series"])
        self.assertEqual(len(names), len(set(names)))
        self.assertGreaterEqual(len(names), 8)


if __name__ == "__main__":
    unittest.main()

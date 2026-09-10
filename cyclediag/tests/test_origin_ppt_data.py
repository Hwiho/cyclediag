from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cyclediag.origin_ppt.decks import DECKS, all_slides, slides_for
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

    def test_named_decks_exist(self) -> None:
        for name in ("dvdq_soc0", "sohq", "resistance", "rest_voltage", "hysteresis", "cv", "lifetime"):
            self.assertIn(name, DECKS)
            self.assertGreaterEqual(len(DECKS[name].metrics), 2)

    def test_sohq_deck_specs(self) -> None:
        tagged = load_tagged()
        deck, slides = slides_for("sohq", tagged=tagged, skip_profiles=True)
        self.assertEqual(deck.id, "sohq")
        kinds = [s["kind"] for s in slides]
        self.assertEqual(kinds[0], "cover")
        self.assertEqual(kinds[-1], "summary")
        names = [g["ole_name"] for s in slides for g in s.get("graphs") or []]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(any(s["kind"] == "graphs" for s in slides))
        for spec in slides:
            for graph in spec.get("graphs") or []:
                self.assertTrue(graph["series"])

    def test_custom_metrics_deck(self) -> None:
        tagged = load_tagged()
        deck, slides = slides_for("sohq", tagged=tagged, metrics=("SoHQ", "CE"))
        self.assertEqual(deck.id, "custom")
        titles = [s["title"] for s in slides if s["kind"] == "graphs"]
        self.assertTrue(any("SoHQ" in t for t in titles))
        self.assertTrue(any(t.startswith("CE") or "CE vs" in t for t in titles))

    def test_unknown_metric_raises(self) -> None:
        tagged = load_tagged()
        with self.assertRaises(KeyError):
            slides_for("sohq", tagged=tagged, metrics=("not_a_real_column",))

    def test_matplotlib_sohq_writes(self) -> None:
        try:
            import pptx  # noqa: F401
        except ImportError:
            self.skipTest("python-pptx not installed")
        import tempfile

        from cyclediag.origin_ppt.matplotlib_slides import build_matplotlib

        tagged = load_tagged()
        deck, slides = slides_for("sohq", tagged=tagged, skip_profiles=True)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sohq.pptx"
            build_matplotlib(slides, out, deck=deck, tagged=tagged)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 8_000)


if __name__ == "__main__":
    unittest.main()

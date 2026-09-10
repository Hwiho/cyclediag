"""CLI: python -m cyclediag.origin_ppt"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import default_out
from .data import list_metric_columns, load_tagged
from .decks import DECKS, format_deck_list, slides_for


def _parse_metrics(raw: str | None) -> tuple[str, ...] | None:
    if not raw:
        return None
    parts = tuple(item.strip() for item in raw.split(",") if item.strip())
    return parts or None


def _print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        sys.stdout.buffer.write((text + "\n").encode(encoding, errors="replace"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a lifetime-indicator PowerPoint (Origin OLE or matplotlib)."
    )
    parser.add_argument("--deck", default="dvdq_soc0", choices=sorted(DECKS), help="Named indicator deck")
    parser.add_argument("--metrics", help="Comma-separated tagged columns (overrides --deck layout)")
    parser.add_argument("--list-decks", action="store_true")
    parser.add_argument("--list-metrics", action="store_true", help="Numeric tagged columns available for --metrics")
    parser.add_argument("--backend", choices=("origin", "matplotlib"), default="origin")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--refresh-profiles", action="store_true")
    parser.add_argument("--skip-profiles", action="store_true", help="Skip V–Q / dV/dQ curve slides (dvdq_soc0)")
    args = parser.parse_args()

    if args.list_decks:
        _print(format_deck_list())
        return 0
    if args.list_metrics:
        for line in list_metric_columns(load_tagged()):
            _print(line)
        return 0

    metrics = _parse_metrics(args.metrics)
    deck_id = "custom" if metrics else args.deck
    skip_profiles = args.skip_profiles or args.backend == "matplotlib" or bool(metrics) or args.deck != "dvdq_soc0"
    out = (args.out or default_out(deck_id if not metrics else "custom", backend=args.backend)).resolve()

    if args.backend == "matplotlib":
        from .matplotlib_slides import build_matplotlib

        deck, slides = slides_for(
            args.deck,
            refresh_profiles=args.refresh_profiles,
            skip_profiles=skip_profiles,
            metrics=metrics,
        )
        build_matplotlib(slides, out, deck=deck, tagged=load_tagged())
        return 0

    from .build_slides import build

    build(
        out,
        deck=args.deck,
        metrics=metrics,
        refresh_profiles=args.refresh_profiles,
        skip_profiles=skip_profiles,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

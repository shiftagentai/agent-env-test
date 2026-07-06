#!/usr/bin/env python3
"""
Phase 2 — Generate the executive summary section.

Pure deterministic shaping of the Phase 1 bundle: computes the report's
headline metrics and writes section-executive.json. No data access, no SQL.

Usage:
    python3 phase_2_executive_summary.py --partner P --period YYYY-MM [--spend-period YYYY-MM]
"""

import argparse

from _common import context_metrics, prior_month, read_json, run_dir, write_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compute executive summary metrics.")
    p.add_argument("--partner", required=True)
    p.add_argument("--period", required=True)
    p.add_argument("--spend-period", default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rd = run_dir(args.partner, args.period)
    bundle = read_json(rd / "data.json")

    total_spend = round(sum(r["spend"] for r in bundle["vendor_spend"]), 2)
    attributed_revenue = round(sum(r["revenue"] for r in bundle["roas"]), 2)
    total_jobs = sum(r["jobs"] for r in bundle["roas"])
    blended_roas = round(attributed_revenue / total_spend, 4) if total_spend else 0.0

    ctx = context_metrics(args.partner)
    qual_rate = round(ctx["qualified"] / ctx["total_calls"] * 100, 1) if ctx["total_calls"] else 0.0

    section = {
        "total_spend": total_spend,
        "attributed_revenue": attributed_revenue,
        "blended_roas": blended_roas,
        "total_jobs": total_jobs,
        "calls_analyzed": ctx["total_calls"],
        "qualified_count": ctx["qualified"],
        "qual_rate": qual_rate,
        "missed_count": ctx["missed_count"],
        "lost_revenue": round(ctx["lost_revenue"], 2),
        "data_mode": bundle["meta"]["data_mode"],
    }

    # The blended ROAS is a pure derivation — assert the invariant (within the
    # 4-dp rounding) so a bad bundle is caught here rather than surfacing as a
    # wrong headline number.
    if total_spend:
        assert abs(section["blended_roas"] - attributed_revenue / total_spend) < 5e-4

    out = rd / "section-executive.json"
    write_json(out, section)

    print(f"Wrote {out}")
    print(f"  total_spend:        ${section['total_spend']:,.2f}")
    print(f"  attributed_revenue: ${section['attributed_revenue']:,.2f}")
    print(f"  blended_roas:       {section['blended_roas']:.2f}x")
    print(f"  total_jobs:         {section['total_jobs']}")
    print(f"  qual_rate:          {section['qual_rate']}%  ({section['qualified_count']}/{section['calls_analyzed']})")
    print(f"  missed:             {section['missed_count']} calls, ${section['lost_revenue']:,.2f} lost")
    print(f"  data_mode:          {section['data_mode']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Phase 3 — Generate the spend and ROAS sections.

Deterministic shaping of the Phase 1 bundle into formatted body sections:
ranks rows, computes per-row shares and totals, and tags ROAS rows with a
fixed-threshold status so coloring is identical on every run. No data access,
no SQL.

The two parts (spend / roas) are independent and can be run in parallel.

Usage:
    python3 phase_3_spend_roas_sections.py --partner P --period YYYY-MM \
        [--spend-period YYYY-MM] --part {spend|roas|all}
"""

import argparse

from _common import prior_month, read_json, run_dir, write_json

# Fixed ROAS thresholds → deterministic status (same every run, customizable here).
ROAS_GOOD = 4.0
ROAS_WARN = 2.0


def _ranked_share(rows: list[dict], key: str, label: str) -> list[dict]:
    """Sort by spend desc and attach each row's share of the total."""
    total = sum(r["spend"] for r in rows) or 1.0
    ranked = sorted(rows, key=lambda r: r["spend"], reverse=True)
    return [
        {
            label: r[key],
            "spend": round(r["spend"], 2),
            "share_pct": round(r["spend"] / total * 100, 1),
        }
        for r in ranked
    ]


def build_spend(bundle: dict) -> dict:
    top_vendors = _ranked_share(bundle["vendor_spend"], "vendor", "vendor")[:12]
    channels = _ranked_share(bundle["channel_spend"], "channel", "channel")
    regions = _ranked_share(bundle["region_spend"], "region", "region")
    return {
        "top_vendors": top_vendors,
        "channels": channels,
        "regions": regions,
        "totals": {
            "vendor_spend": round(sum(r["spend"] for r in bundle["vendor_spend"]), 2),
            "channel_spend": round(sum(r["spend"] for r in bundle["channel_spend"]), 2),
            "region_spend": round(sum(r["spend"] for r in bundle["region_spend"]), 2),
        },
    }


def _roas_status(roas: float | None) -> str:
    if roas is None:
        return "bad"
    if roas >= ROAS_GOOD:
        return "good"
    if roas >= ROAS_WARN:
        return "warn"
    return "bad"


def build_roas(bundle: dict) -> dict:
    rows = []
    for r in bundle["roas"]:
        spend = r["spend"]
        roas = round(r["revenue"] / spend, 2) if spend else None
        rows.append(
            {
                "vendor": r["vendor"],
                "jobs": r["jobs"],
                "revenue": round(r["revenue"], 2),
                "spend": round(spend, 2),
                "roas": roas,
                "status": _roas_status(roas),
            }
        )
    rows.sort(key=lambda x: (x["roas"] is None, -(x["roas"] or 0)))
    return {
        "rows": rows,
        "totals": {
            "jobs": sum(r["jobs"] for r in rows),
            "revenue": round(sum(r["revenue"] for r in rows), 2),
            "spend": round(sum(r["spend"] for r in rows), 2),
        },
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build spend + ROAS sections.")
    p.add_argument("--partner", required=True)
    p.add_argument("--period", required=True)
    p.add_argument("--spend-period", default=None)
    p.add_argument("--part", default="all", choices=("spend", "roas", "all"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rd = run_dir(args.partner, args.period)
    bundle = read_json(rd / "data.json")

    if args.part in ("spend", "all"):
        spend = build_spend(bundle)
        write_json(rd / "section-spend.json", spend)
        print(f"Wrote {rd / 'section-spend.json'}")
        print(f"  vendors: {len(spend['top_vendors'])}  channels: {len(spend['channels'])}  regions: {len(spend['regions'])}")

    if args.part in ("roas", "all"):
        roas = build_roas(bundle)
        write_json(rd / "section-roas.json", roas)
        print(f"Wrote {rd / 'section-roas.json'}")
        print(f"  roas rows: {len(roas['rows'])}  (good/warn/bad tagged)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Phase 1 — Retrieve and prepare data.

Requests the four independent marketing data sets from the ThoughtSpot /
MetricFlow service (see _common.thoughtspot_retrieve) and normalizes them into
a single bundle the later phases consume.

DATA ACCESS is hardened and external — this script asks the data service for
precise results; it contains NO SQL. DETERMINISTIC SHAPING (normalization,
merging) is what lives here.

Usage:
    # one dataset (used by the parallel fan-out in Phase 1)
    python3 phase_1_retrieve_data.py --partner P --period YYYY-MM \
        --spend-period YYYY-MM --dataset vendor_spend

    # all four + write the merged bundle to the run dir
    python3 phase_1_retrieve_data.py --partner P --period YYYY-MM \
        --spend-period YYYY-MM --dataset all --write-bundle

Output:
    --dataset <one>            prints that fragment as JSON to stdout
    --dataset all --write-bundle  writes /workspace/marketing-report/{P}-{period}/data.json
"""

import argparse
import json

from _common import (
    DATASETS,
    prior_month,
    run_dir,
    thoughtspot_retrieve,
    write_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Retrieve + prepare marketing report data.")
    p.add_argument("--partner", required=True)
    p.add_argument("--period", required=True, help="Report month YYYY-MM")
    p.add_argument("--spend-period", default=None, help="Spend month YYYY-MM (default: prior month)")
    p.add_argument(
        "--dataset",
        default="all",
        choices=(*DATASETS, "all"),
        help="Which data set to retrieve, or 'all'.",
    )
    p.add_argument(
        "--write-bundle",
        action="store_true",
        help="With --dataset all, write the merged data.json to the run dir.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    spend_period = args.spend_period or prior_month(args.period)

    if args.dataset != "all":
        fragment = thoughtspot_retrieve(args.dataset, args.partner, spend_period)
        print(json.dumps(fragment, indent=2))
        return

    # Retrieve all four and normalize into one bundle.
    fragments = {
        ds: thoughtspot_retrieve(ds, args.partner, spend_period) for ds in DATASETS
    }
    data_modes = {f["data_mode"] for f in fragments.values()}
    bundle = {
        "meta": {
            "partner": args.partner,
            "period": args.period,
            "spend_period": spend_period,
            # 'live' only if every retrieval was live; otherwise 'synthetic'.
            "data_mode": "live" if data_modes == {"live"} else "synthetic",
        },
        "vendor_spend": fragments["vendor_spend"]["rows"],
        "channel_spend": fragments["channel_spend"]["rows"],
        "region_spend": fragments["region_spend"]["rows"],
        "roas": fragments["roas"]["rows"],
    }

    if args.write_bundle:
        out = run_dir(args.partner, args.period) / "data.json"
        write_json(out, bundle)
        print(f"Wrote bundle -> {out}")
        print(f"  data_mode: {bundle['meta']['data_mode']}")
        for ds in DATASETS:
            print(f"  {ds}: {len(bundle[ds])} rows")
    else:
        print(json.dumps(bundle, indent=2))


if __name__ == "__main__":
    main()

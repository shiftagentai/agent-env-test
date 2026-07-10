#!/usr/bin/env python3
"""
Shared helpers for the marketing-performance-report phase scripts.

Two responsibilities live here, and they map directly to the architectural
line this skill is built to demonstrate:

  1. DATA ACCESS (hardened, external)  -> `thoughtspot_retrieve()`
     The specific data sets are fetched from a ThoughtSpot / MetricFlow data
     service that already exists. The agent NEVER writes SQL; it asks the
     service for precise results for the given parameters. In this POC the
     service call is hand-waved: if a real endpoint is configured via env vars
     it would be called here; otherwise we fall back to a clearly-labeled
     synthetic block so the rest of the pipeline can run end-to-end.

  2. RUN PLUMBING (paths, partner registry, io)
     The per-run working directory under /workspace, the partner branding
     registry, and JSON read/write helpers the phase scripts share.

There is intentionally NO SQL anywhere in this skill.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Run plumbing — per-run working directory
# ---------------------------------------------------------------------------

WORKSPACE_ROOT = os.environ.get("SHIFTAGENT_WORKSPACE", "/workspace")


def run_dir(partner: str, period: str) -> Path:
    """The per-run working dir that phases hand artifacts through."""
    d = Path(WORKSPACE_ROOT) / "marketing-report" / f"{partner}-{period}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def prior_month(period: str) -> str:
    y, m = (int(x) for x in period.split("-"))
    pm, py = (12, y - 1) if m == 1 else (m - 1, y)
    return f"{py}-{pm:02d}"


# ---------------------------------------------------------------------------
# Partner registry — deterministic, per-tenant branding (customizable here,
# not in a system tool). Mirrors the reference POC's partner config.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Partner:
    key: str
    name: str
    short: str
    tagline: str
    regions: str
    cover_bg: str
    navy: str
    accent: str
    good: str = "#10B981"
    warn: str = "#F59E0B"
    bad: str = "#EF4444"


PARTNERS: dict[str, Partner] = {
    "lees-air": Partner(
        key="lees-air",
        name="Lee's Air, Plumbing, Heating & Roofing",
        short="LEE'S",
        tagline="Local and trusted Comfort Experts — Serving Sacramento and Fresno since 1981",
        regions="California · Nevada · Texas · Arizona",
        cover_bg="#0F2D52",
        navy="#0A2540",
        accent="#C9A227",
    ),
    "a1-garage": Partner(
        key="a1-garage",
        name="A1 Garage Door Service",
        short="A1",
        tagline="Serving the Entire South Bay Areas",
        regions="South Bay · Los Angeles County",
        cover_bg="#1D2C31",
        navy="#1D2C31",
        accent="#A40000",
        bad="#C0392B",
    ),
}


def get_partner(key: str) -> Partner:
    p = PARTNERS.get(key)
    if not p:
        known = ", ".join(PARTNERS)
        raise SystemExit(f"Unknown partner '{key}'. Known partners: {known}")
    return p


def partner_dict(p: Partner) -> dict:
    return asdict(p)


# ---------------------------------------------------------------------------
# DATA ACCESS — hardened, external. Hand-waved ThoughtSpot / MetricFlow client.
# ---------------------------------------------------------------------------

# Datasets the report is built from. Each is an independent retrieval — which is
# why Phase 1 fans them out in parallel.
DATASETS = ("vendor_spend", "channel_spend", "region_spend", "roas")


def thoughtspot_retrieve(dataset: str, partner: str, spend_period: str) -> dict:
    """
    Request a single precise data set from the ThoughtSpot / MetricFlow service.

    In production this issues an authenticated request to the data service for
    the exact parameters (partner, period, dataset) and returns the service's
    result verbatim. The credential and endpoint are resolved at the network
    boundary — they are NOT visible to this code, and there is NO SQL here.

    If `THOUGHTSPOT_BASE_URL` is configured we would call it; in this POC it is
    not, so we return a clearly-labeled synthetic block so the deterministic
    presentation layer (phases 2–5) can run end to end. The fallback is marked
    `"data_mode": "synthetic"` so nothing downstream ever mistakes it for live
    data or invents figures of its own.
    """
    if dataset not in DATASETS:
        raise SystemExit(f"Unknown dataset '{dataset}'. Known: {', '.join(DATASETS)}")

    # Validate the partner up front — never silently serve another partner's
    # data for an unknown key.
    get_partner(partner)

    base_url = os.environ.get("THOUGHTSPOT_BASE_URL")
    if base_url:
        # Real path (not exercised in this POC): the data service owns retrieval.
        #   payload = thoughtspot_client.query_view(
        #       view=f"marketing.{dataset}",
        #       params={"partner": partner, "period": spend_period},
        #   )
        # No SQL is constructed here — the named view + params are all we pass.
        raise SystemExit(
            "THOUGHTSPOT_BASE_URL is set but the live client is not bundled in "
            "this POC. Unset it to use the synthetic fallback."
        )

    rows = _synthetic(dataset, partner)
    return {"dataset": dataset, "data_mode": "synthetic", "rows": rows}


def _synthetic(dataset: str, partner: str) -> list[dict]:
    """Labeled mock results, shaped exactly like the real service would return."""
    seeds = _SYNTHETIC_SEED.get(partner, _SYNTHETIC_SEED["a1-garage"])
    return seeds[dataset]


# Synthetic seed data — shaped like ThoughtSpot/MetricFlow results, used only as
# the labeled fallback. Numbers are illustrative, not real.
_SYNTHETIC_SEED: dict[str, dict[str, list[dict]]] = {
    "lees-air": {
        "vendor_spend": [
            {"vendor": "Meta / Facebook", "spend": 318_420.55},
            {"vendor": "Google Ads", "spend": 197_310.10},
            {"vendor": "eLocal", "spend": 67_240.00},
            {"vendor": "Yelp", "spend": 56_180.25},
            {"vendor": "Angi", "spend": 41_905.00},
            {"vendor": "Local Services Ads", "spend": 33_120.40},
            {"vendor": "Nextdoor", "spend": 18_660.00},
            {"vendor": "Direct Mail", "spend": 14_280.00},
        ],
        "channel_spend": [
            {"channel": "Digital — Paid Social", "spend": 337_080.55},
            {"channel": "Digital — Paid Search", "spend": 230_430.50},
            {"channel": "Directories & Marketplaces", "spend": 165_505.25},
            {"channel": "Offline — Direct Mail", "spend": 14_280.00},
        ],
        "region_spend": [
            {"region": "Sacramento", "spend": 312_400.00},
            {"region": "Fresno", "spend": 248_900.00},
            {"region": "Las Vegas", "spend": 121_500.00},
            {"region": "Phoenix", "spend": 64_496.30},
        ],
        "roas": [
            {"vendor": "Google Ads", "jobs": 412, "revenue": 1_284_300.0, "spend": 197_310.10},
            {"vendor": "Meta / Facebook", "jobs": 521, "revenue": 1_010_450.0, "spend": 318_420.55},
            {"vendor": "Local Services Ads", "jobs": 188, "revenue": 402_900.0, "spend": 33_120.40},
            {"vendor": "Yelp", "jobs": 96, "revenue": 121_700.0, "spend": 56_180.25},
            {"vendor": "eLocal", "jobs": 74, "revenue": 61_300.0, "spend": 67_240.00},
        ],
    },
    "a1-garage": {
        "vendor_spend": [
            {"vendor": "Google Ads", "spend": 88_400.00},
            {"vendor": "Meta / Facebook", "spend": 52_100.00},
            {"vendor": "Yelp", "spend": 21_750.00},
            {"vendor": "Local Services Ads", "spend": 18_900.00},
            {"vendor": "Nextdoor", "spend": 9_300.00},
        ],
        "channel_spend": [
            {"channel": "Digital — Paid Search", "spend": 107_300.00},
            {"channel": "Digital — Paid Social", "spend": 52_100.00},
            {"channel": "Directories & Marketplaces", "spend": 21_750.00},
        ],
        "region_spend": [
            {"region": "South Bay", "spend": 118_600.00},
            {"region": "Los Angeles County", "spend": 71_850.00},
        ],
        "roas": [
            {"vendor": "Google Ads", "jobs": 196, "revenue": 612_400.0, "spend": 88_400.00},
            {"vendor": "Meta / Facebook", "jobs": 121, "revenue": 246_900.0, "spend": 52_100.00},
            {"vendor": "Local Services Ads", "jobs": 64, "revenue": 158_200.0, "spend": 18_900.00},
            {"vendor": "Yelp", "jobs": 28, "revenue": 39_400.0, "spend": 21_750.00},
        ],
    },
}


# Call-intelligence / missed-revenue context metrics are not part of the four
# parallel retrievals; they are small partner-level facts the executive summary
# needs. Hand-waved the same way — sourced from the data service in production.
_CONTEXT_SEED: dict[str, dict] = {
    "lees-air": {"total_calls": 4820, "qualified": 3110, "missed_count": 392, "lost_revenue": 588_000.0},
    "a1-garage": {"total_calls": 1640, "qualified": 1010, "missed_count": 121, "lost_revenue": 181_500.0},
}


def context_metrics(partner: str) -> dict:
    return _CONTEXT_SEED.get(partner, _CONTEXT_SEED["a1-garage"])

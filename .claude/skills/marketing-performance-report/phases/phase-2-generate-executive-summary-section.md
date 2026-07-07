# Phase 2 — Generate the executive summary section

**You are here because Phase 1 sent you.** Phase 1 wrote `data.json`. Do this phase, then follow the "Next step" line.

## Goal

Compute the report's headline executive metrics deterministically from the bundle and write `section-executive.json`.

This is pure deterministic shaping of data already retrieved in Phase 1 — no new data access.

## Run

```bash
python3 .claude/skills/marketing-performance-report/scripts/phase_2_executive_summary.py \
  --partner {partner} --period {period} --spend-period {spend_period}
```

The script reads `/workspace/marketing-report/{partner}-{period}/data.json` and writes `section-executive.json` to the same dir. It prints the computed metrics to stdout so you can sanity-check them:

- `total_spend` — total marketing spend for the spend period
- `attributed_revenue` — revenue attributed across ROAS vendors
- `blended_roas` — attributed revenue ÷ total spend
- `calls_analyzed`, `qualified_count`, `qual_rate`
- `missed_count`, `lost_revenue`
- `total_jobs`

Every figure is derived arithmetically from the bundle — the script does not re-fetch anything.

## Verify

Glance at the printed metrics. `blended_roas` should equal `attributed_revenue / total_spend` (the script asserts this). If `total_spend` is `0`, the bundle is empty — go back to Phase 1 rather than proceeding with a divide-by-zero section.

---

**Next step:** read [phase-3-generate-spend-and-roas-sections.md](phase-3-generate-spend-and-roas-sections.md) and continue. Do not open phases 4–5 yet.

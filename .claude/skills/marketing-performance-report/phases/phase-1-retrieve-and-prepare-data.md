# Phase 1 — Retrieve and prepare data

**You are here because SKILL.md sent you.** Do this phase, then follow the "Next step" line at the bottom. Do not skip ahead to later phase files.

## Goal

Retrieve the four independent marketing data sets for `{partner}` / `{spend_period}` from the **ThoughtSpot / MetricFlow** service and normalize them into a single `data.json` bundle the later phases consume.

The four data sets are independent retrievals, so this is the phase to **fan out in parallel**.

## What to retrieve (parallel)

Spawn **four subagents in a single message** so they run concurrently — one per data set. Each subagent runs the retrieval script with its `--dataset` selector and writes one JSON artifact. They share no context, so give each a short, self-contained prompt.

| Subagent | Dataset | Command |
|---|---|---|
| vendor-spend | Top vendor spend | `python3 .claude/skills/marketing-performance-report/scripts/phase_1_retrieve_data.py --partner {partner} --period {period} --spend-period {spend_period} --dataset vendor_spend` |
| channel-spend | GL / channel spend | `… --dataset channel_spend` |
| region-spend | Spend by region | `… --dataset region_spend` |
| roas | ROAS inputs (jobs, revenue, spend by vendor) | `… --dataset roas` |

Each command requests **precise results for the given parameters** from ThoughtSpot/MetricFlow and prints a JSON fragment to stdout. There is no SQL here and you must not add any — the service owns retrieval.

## Join the fragments

When all four return, merge them into the canonical bundle:

```bash
python3 .claude/skills/marketing-performance-report/scripts/phase_1_retrieve_data.py \
  --partner {partner} --period {period} --spend-period {spend_period} --dataset all --write-bundle
```

`--dataset all --write-bundle` performs all four retrievals and writes the merged bundle to:

```
/workspace/marketing-report/{partner}-{period}/data.json
```

(If you prefer not to fan out — e.g. for a quick single-agent run — `--dataset all --write-bundle` on its own produces the identical bundle sequentially. The parallel path is purely to expedite.)

## Verify

Confirm the bundle exists and has all four sections plus a `meta` block:

```bash
python3 -c "import json; d=json.load(open('/workspace/marketing-report/{partner}-{period}/data.json')); print(sorted(d.keys()))"
```

Expect: `['channel_spend', 'meta', 'region_spend', 'roas', 'vendor_spend']`. The `meta.data_mode` field is `live` when ThoughtSpot/MetricFlow returned data and `synthetic` when it fell back to the labeled mock block — never invent figures yourself either way.

---

**Next step:** read [phase-2-generate-executive-summary-section.md](phase-2-generate-executive-summary-section.md) and continue. Do not open phases 3–5 yet.

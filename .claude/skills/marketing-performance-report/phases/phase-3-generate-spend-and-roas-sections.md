# Phase 3 — Generate the spend and ROAS sections

**You are here because Phase 2 sent you.** Do this phase, then follow the "Next step" line.

## Goal

Shape the detailed body sections — vendor spend, channel/GL spend, region spend, and ROAS-by-vendor — into formatted tables and write `section-spend.json` and `section-roas.json`.

These two sections are independent of each other, so you may **fan them out as two parallel subagents** to expedite. They both read the same `data.json` and write separate artifacts, so there is no conflict.

## Run (parallel)

Issue both in a single message:

| Subagent | Command | Writes |
|---|---|---|
| spend-sections | `python3 .claude/skills/marketing-performance-report/scripts/phase_3_spend_roas_sections.py --partner {partner} --period {period} --spend-period {spend_period} --part spend` | `section-spend.json` |
| roas-section | `python3 .claude/skills/marketing-performance-report/scripts/phase_3_spend_roas_sections.py --partner {partner} --period {period} --spend-period {spend_period} --part roas` | `section-roas.json` |

(Or run `--part all` in one shot for the sequential path — it produces both artifacts identically.)

Each part deterministically:

- ranks and formats the rows (top-N vendors, channels sorted by spend, regions, ROAS by vendor),
- computes per-row shares and totals,
- tags ROAS rows with a status (`good` / `warn` / `bad`) using fixed thresholds so the coloring is identical every run.

All of this is shaping of Phase 1 data — no retrieval, no SQL.

## Verify

```bash
python3 -c "import json; s=json.load(open('/workspace/marketing-report/{partner}-{period}/section-spend.json')); print('vendors:', len(s['top_vendors']), 'channels:', len(s['channels']), 'regions:', len(s['regions']))"
python3 -c "import json; r=json.load(open('/workspace/marketing-report/{partner}-{period}/section-roas.json')); print('roas rows:', len(r['rows']))"
```

---

**Next step:** read [phase-4-generate-html-file.md](phase-4-generate-html-file.md) and continue. Do not open phase 5 yet.

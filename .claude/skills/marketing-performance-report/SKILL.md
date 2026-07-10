---
name: marketing-performance-report
description: Generates a multi-page Marketing Performance Analysis report (spend, ROAS, vendor/channel/region breakdowns) for a partner and period, then renders it to HTML and PDF. Use when the user invokes /marketing-performance-report or asks for a marketing performance / ROAS / marketing spend report for a partner. The report is large and is built in ordered, separately-loaded phases — read each phase file only after completing the previous one.
---

# marketing-performance-report

Produces a partner-branded **Marketing Performance Analysis** report — the kind of 20–30 page deliverable that pairs heavy data retrieval with a heavy deterministic layer so every run comes out with the same structure, the same sections, and the same shape.

This skill is deliberately split across **phase files** in `phases/`, each with a counterpart script in `scripts/`. **This file gives you only enough context to start.** Do **not** read all the phase files up front — load each one only when the previous phase tells you to. This keeps the working context small and focused, one phase at a time, exactly the way a large report should be assembled.

---

## What this skill does and does NOT do

This skill draws a hard line between **data access** and **data presentation**:

- **Data access is hardened and external — NOT the agent's job.** The specific data sets (marketing spend, vendor rollups, GL/channel balances, ROAS inputs) are retrieved through a **ThoughtSpot / MetricFlow** data service that already exists. The scripts call that service for precise results for the given parameters. **There are no SQL queries in this skill, and you must never write or improvise one.** If you find yourself wanting to query a database directly, stop — that data comes from ThoughtSpot/MetricFlow.
- **Data presentation is deterministic and lives here.** What the scripts *do* own is the deterministic shaping of the returned data — normalizing it, computing the report's metrics, and formatting it into the exact tables, sections, and layout the report requires. That deterministic shaping is the whole point of putting it in a skill: it can be customized per tenant without a code release.

Precise data in (ThoughtSpot/MetricFlow); deterministic, customizable presentation out (these scripts).

---

## Inputs

The user (or caller) supplies:

- `partner` — partner slug, e.g. `lees-air` or `a1-garage`.
- `period` — reporting month as `YYYY-MM`, e.g. `2026-05`.
- `spend_period` — optional; the month whose spend feeds the report. Defaults to the month before `period`.

Every phase script accepts `--partner`, `--period`, and `--spend-period` and reads/writes its intermediate artifacts under a per-run working directory:

```
/workspace/marketing-report/{partner}-{period}/
```

This working dir is the hand-off channel between phases — each phase writes a JSON (or HTML/PDF) artifact the next phase reads. Write deliverables to `/workspace/` (the git-synced workspace root), **never** into `.claude/skills/`.

---

## How to run — the daisy chain

Work the phases **in order**, and open each phase file **only when you reach it**:

1. **Start with Phase 1.** Read [phases/phase-1-retrieve-and-prepare-data.md](phases/phase-1-retrieve-and-prepare-data.md) and do what it says.
2. When a phase finishes, it ends with a **"Next step"** line naming the next phase file. Read that file then — and not before.
3. Repeat until the final phase produces the PDF.

The phases are:

| Phase | File | Produces |
|---|---|---|
| 1 | `phases/phase-1-retrieve-and-prepare-data.md` | Normalized data bundle (`data.json`) |
| 2 | `phases/phase-2-generate-executive-summary-section.md` | `section-executive.json` |
| 3 | `phases/phase-3-generate-spend-and-roas-sections.md` | `section-spend.json`, `section-roas.json` |
| 4 | `phases/phase-4-generate-html-file.md` | `marketing-analysis.html` |
| 5 | `phases/phase-5-generate-pdf-file.md` | `marketing-analysis.pdf` |

You do not need to know the details of phases 2–5 yet. Phase 1 will hand you Phase 2.

---

## Parallelism — expedite the independent work

**Phase 1 is the one place to fan out.** The four data sets the report needs — vendor spend, channel/GL spend, region spend, and ROAS inputs — are independent retrievals. Phase 1 tells you to spawn them as **parallel subagents in a single message** (not sequentially), then join their outputs into one bundle. Phases 2 and 3 also describe independent sections that can be generated concurrently. Each of those phase files spells out exactly what to fan out and what to wait for; follow the instructions there rather than parallelizing on your own.

Phases 4 and 5 are sequential — HTML must exist before the PDF is rendered from it.

---

## Output

The final deliverables land in the per-run working dir:

```
/workspace/marketing-report/{partner}-{period}/marketing-analysis.html
/workspace/marketing-report/{partner}-{period}/marketing-analysis.pdf
```

Report the two paths to the user when Phase 5 completes.

---

## Anti-patterns

- **Do not read all phase files at once.** The separation is intentional — load each phase only when the prior one points you to it. Reading ahead defeats the progressive, context-light design.
- **Do not write SQL or query a database directly.** All data comes from the ThoughtSpot/MetricFlow service the scripts already call. No exceptions.
- **Do not fabricate figures.** If a retrieval returns no data, the scripts fall back to a clearly-labeled synthetic block; never invent numbers in the narrative.
- **Do not move data access into the agent.** The agent orchestrates phases and shapes presentation; it does not become the data pipeline.
- **Do not write intermediate artifacts into `.claude/skills/`.** Everything for a run goes under `/workspace/marketing-report/{partner}-{period}/`.

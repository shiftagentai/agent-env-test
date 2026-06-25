# Phase 4 — Generate the HTML file

**You are here because Phase 3 sent you.** All three section artifacts now exist (`section-executive.json`, `section-spend.json`, `section-roas.json`). Do this phase, then follow the "Next step" line.

## Goal

Assemble the section artifacts into a single partner-branded `marketing-analysis.html` — cover page, executive summary, spend sections, ROAS table, footer — with deterministic layout and the partner's color palette.

This phase is **sequential** (it depends on all prior sections) — do not fan out.

## Run

```bash
python3 .claude/skills/marketing-performance-report/scripts/phase_4_render_html.py \
  --partner {partner} --period {period} --spend-period {spend_period}
```

The script reads `data.json` + the three `section-*.json` files and writes:

```
/workspace/marketing-report/{partner}-{period}/marketing-analysis.html
```

Branding (partner name, tagline, regions, colors) comes from a small built-in partner registry in the script — the same deterministic, per-tenant customization point we want living in the skill, not in a system tool. The HTML is fully self-contained (inline CSS), so the PDF phase can render it without external assets.

## Verify

```bash
test -s /workspace/marketing-report/{partner}-{period}/marketing-analysis.html && echo "HTML written" || echo "MISSING"
```

Open or grep the file to confirm the partner name and the section headings are present.

---

**Next step:** read [phase-5-generate-pdf-file.md](phase-5-generate-pdf-file.md) and finish the report.

# Phase 5 — Generate the PDF file

**You are here because Phase 4 sent you.** `marketing-analysis.html` now exists. This is the final phase.

## Goal

Render the HTML to a print-ready `marketing-analysis.pdf`.

## Run

```bash
python3 .claude/skills/marketing-performance-report/scripts/phase_5_render_pdf.py \
  --partner {partner} --period {period}
```

The script renders the HTML to PDF using the platform's headless-Chrome rendering service (the same hand-waved "it already exists" posture as data retrieval — the skill does not bundle a browser). It writes:

```
/workspace/marketing-report/{partner}-{period}/marketing-analysis.pdf
```

If the rendering service is not wired up in the current environment, the script exits with a clear message and leaves a `.pdf.txt` placeholder noting that the HTML is complete and ready to render — it does **not** fail the whole report or fabricate a PDF.

## Verify and report

```bash
ls -la /workspace/marketing-report/{partner}-{period}/
```

Report **both** deliverable paths to the user:

```
/workspace/marketing-report/{partner}-{period}/marketing-analysis.html
/workspace/marketing-report/{partner}-{period}/marketing-analysis.pdf
```

That completes the Marketing Performance Analysis report. There is no next phase.

#!/usr/bin/env python3
"""
Phase 5 — Generate the PDF file.

Renders the Phase 4 HTML to a print-ready PDF using the platform's headless
rendering service. The browser is NOT bundled in this skill — same hand-waved
"it already exists" posture as data retrieval.

If no rendering backend is available in the current environment, this exits
cleanly with a placeholder note rather than failing the report or fabricating
a PDF. No data access, no SQL.

Usage:
    python3 phase_5_render_pdf.py --partner P --period YYYY-MM

Output:
    /workspace/marketing-report/{P}-{period}/marketing-analysis.pdf  (when a backend exists)
    /workspace/marketing-report/{P}-{period}/marketing-analysis.pdf.txt  (placeholder otherwise)
"""

import argparse
import shutil
import subprocess
import sys

from _common import run_dir


def render_with_chrome(html_path, pdf_path) -> bool:
    """Try a headless-Chrome print-to-PDF. Returns True on success."""
    chrome = (
        shutil.which("google-chrome")
        or shutil.which("chromium")
        or shutil.which("chromium-browser")
        or shutil.which("chrome")
    )
    if not chrome:
        return False
    try:
        subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                f"--print-to-pdf={pdf_path}",
                "--no-pdf-header-footer",
                f"file://{html_path}",
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
        return pdf_path.exists() and pdf_path.stat().st_size > 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def parse_args() -> argparse.Namespace:
    a = argparse.ArgumentParser(description="Render the report PDF.")
    a.add_argument("--partner", required=True)
    a.add_argument("--period", required=True)
    return a.parse_args()


def main() -> None:
    args = parse_args()
    rd = run_dir(args.partner, args.period)
    html_path = rd / "marketing-analysis.html"
    pdf_path = rd / "marketing-analysis.pdf"

    if not html_path.exists():
        print(f"ERROR: {html_path} not found — run Phase 4 first.", file=sys.stderr)
        sys.exit(1)

    if render_with_chrome(html_path, pdf_path):
        print(f"Wrote {pdf_path}  ({pdf_path.stat().st_size:,} bytes)")
        return

    # No rendering backend — leave a clear placeholder, do not fail or fake it.
    placeholder = pdf_path.with_suffix(".pdf.txt")
    placeholder.write_text(
        "PDF not rendered: no headless-Chrome backend was available in this "
        "environment. The complete, print-ready HTML is at:\n"
        f"  {html_path}\n"
        "In production the platform's headless rendering service produces the "
        "PDF from this HTML.\n"
    )
    print("No headless-Chrome backend available — HTML is complete and ready to render.")
    print(f"  HTML:        {html_path}")
    print(f"  Placeholder: {placeholder}")


if __name__ == "__main__":
    main()

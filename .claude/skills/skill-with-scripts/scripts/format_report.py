#!/usr/bin/env python3
"""
Deterministic AI news report formatter.
Reads JSON from stdin, writes a formatted report to stdout.

Input JSON schema:
{
  "date": "YYYY-MM-DD",
  "sections": [
    {"title": "...", "bullets": ["...", "..."]}
  ]
}

Sections are always rendered in the order they appear in the input array,
which the caller fixes to: Anthropic → OpenAI → Google DeepMind → AI Community.
"""

import json
import sys
import textwrap

REPORT_WIDTH = 72
SECTION_ORDER = ["Anthropic", "OpenAI", "Google DeepMind", "AI Community"]


def divider(char="="):
    return char * REPORT_WIDTH


def render_section(title: str, bullets: list[str]) -> str:
    lines = []
    lines.append(divider("-"))
    lines.append(f"  {title.upper()}")
    lines.append(divider("-"))
    if not bullets:
        lines.append("  (no items reported)")
    else:
        for i, bullet in enumerate(bullets, start=1):
            indent = "     "
            wrapped = textwrap.fill(
                bullet,
                width=REPORT_WIDTH - 4,
                initial_indent=f"  {i}. ",
                subsequent_indent=indent,
            )
            lines.append(wrapped)
    lines.append("")
    return "\n".join(lines)


def render_report(data: dict) -> str:
    date = data.get("date", "unknown date")
    raw_sections = {s["title"]: s.get("bullets", []) for s in data.get("sections", [])}

    lines = []
    lines.append(divider())
    lines.append(f"  AI NEWS BRIEFING — {date}")
    lines.append(divider())
    lines.append("")

    for title in SECTION_ORDER:
        bullets = raw_sections.get(title, [])
        lines.append(render_section(title, bullets))

    lines.append(divider())
    total = sum(len(s.get("bullets", [])) for s in data.get("sections", []))
    lines.append(f"  {total} item(s) across {len(SECTION_ORDER)} sections.")
    lines.append(divider())

    return "\n".join(lines)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON input — {e}", file=sys.stderr)
        sys.exit(1)

    print(render_report(data))


if __name__ == "__main__":
    main()

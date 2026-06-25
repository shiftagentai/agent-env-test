#!/usr/bin/env python3
"""
Phase 4 — Generate the HTML file.

Assembles the section artifacts (executive, spend, roas) into one
partner-branded, self-contained HTML report. Deterministic layout + the
partner's palette from the registry in _common. No data access, no SQL.

Usage:
    python3 phase_4_render_html.py --partner P --period YYYY-MM [--spend-period YYYY-MM]

Output:
    /workspace/marketing-report/{P}-{period}/marketing-analysis.html
"""

import argparse
import html

from _common import get_partner, read_json, run_dir


def money(n: float) -> str:
    return f"${n:,.0f}"


def esc(s: str) -> str:
    return html.escape(str(s))


def _rows_table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def build_html(partner, meta, ex, spend, roas) -> str:
    p = partner
    mode_banner = (
        ""
        if meta["data_mode"] == "live"
        else '<div class="banner">SAMPLE DATA — figures are synthetic (no live data source configured)</div>'
    )

    vendor_rows = [
        [esc(r["vendor"]), money(r["spend"]), f'{r["share_pct"]}%']
        for r in spend["top_vendors"]
    ]
    channel_rows = [
        [esc(r["channel"]), money(r["spend"]), f'{r["share_pct"]}%']
        for r in spend["channels"]
    ]
    region_rows = [
        [esc(r["region"]), money(r["spend"]), f'{r["share_pct"]}%']
        for r in spend["regions"]
    ]
    roas_rows = [
        [
            esc(r["vendor"]),
            f'{r["jobs"]:,}',
            money(r["revenue"]),
            money(r["spend"]),
            f'<span class="pill {r["status"]}">{("—" if r["roas"] is None else str(r["roas"]) + "x")}</span>',
        ]
        for r in roas["rows"]
    ]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Marketing Performance Analysis — {esc(p.name)}</title>
<style>
  @page {{ size: letter; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; color: #1c2530; }}
  .cover {{ background: {p.cover_bg}; color: #fff; padding: 120px 64px; min-height: 100vh; }}
  .cover .kicker {{ letter-spacing: .28em; font-size: 12px; text-transform: uppercase; opacity: .8; }}
  .cover h1 {{ font-size: 46px; line-height: 1.05; margin: 18px 0 12px; max-width: 16ch; }}
  .cover .accent {{ height: 5px; width: 90px; background: {p.accent}; margin: 24px 0; }}
  .cover .tagline {{ font-size: 17px; opacity: .9; max-width: 52ch; }}
  .cover .regions {{ margin-top: 10px; font-size: 14px; opacity: .75; }}
  .cover .period {{ margin-top: 40px; font-size: 14px; opacity: .85; }}
  section {{ padding: 48px 64px; border-top: 1px solid #e6eaf0; page-break-inside: avoid; }}
  h2 {{ color: {p.navy}; font-size: 24px; border-left: 5px solid {p.accent}; padding-left: 14px; margin: 0 0 22px; }}
  .cards {{ display: flex; flex-wrap: wrap; gap: 16px; }}
  .card {{ flex: 1 1 180px; border: 1px solid #e6eaf0; border-radius: 10px; padding: 18px; }}
  .card .label {{ font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: #6b7e96; }}
  .card .value {{ font-size: 26px; font-weight: 700; color: {p.navy}; margin-top: 6px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 8px; }}
  th {{ text-align: left; background: {p.navy}; color: #fff; padding: 9px 12px; font-size: 12px; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #eef1f5; }}
  tbody tr:nth-child(even) td {{ background: #f7f9fc; }}
  .pill {{ padding: 2px 9px; border-radius: 999px; font-weight: 600; font-size: 12px; color: #fff; }}
  .pill.good {{ background: {p.good}; }}
  .pill.warn {{ background: {p.warn}; }}
  .pill.bad {{ background: {p.bad}; }}
  .banner {{ background: #fff7e6; color: #7c410c; border: 1px solid #e8a06a; padding: 10px 16px; font-size: 13px; }}
  footer {{ padding: 28px 64px; color: #6b7e96; font-size: 12px; border-top: 1px solid #e6eaf0; }}
</style>
</head>
<body>
  {mode_banner}
  <div class="cover">
    <div class="kicker">Marketing Performance Analysis</div>
    <h1>{esc(p.name)}</h1>
    <div class="accent"></div>
    <div class="tagline">{esc(p.tagline)}</div>
    <div class="regions">{esc(p.regions)}</div>
    <div class="period">Reporting period {esc(meta["period"])} · spend period {esc(meta["spend_period"])}</div>
  </div>

  <section>
    <h2>Executive Summary</h2>
    <div class="cards">
      <div class="card"><div class="label">Total Spend</div><div class="value">{money(ex["total_spend"])}</div></div>
      <div class="card"><div class="label">Attributed Revenue</div><div class="value">{money(ex["attributed_revenue"])}</div></div>
      <div class="card"><div class="label">Blended ROAS</div><div class="value">{ex["blended_roas"]:.2f}x</div></div>
      <div class="card"><div class="label">Jobs Attributed</div><div class="value">{ex["total_jobs"]:,}</div></div>
    </div>
    <div class="cards" style="margin-top:16px;">
      <div class="card"><div class="label">Calls Analyzed</div><div class="value">{ex["calls_analyzed"]:,}</div></div>
      <div class="card"><div class="label">Qualified Rate</div><div class="value">{ex["qual_rate"]}%</div></div>
      <div class="card"><div class="label">Missed Calls</div><div class="value">{ex["missed_count"]:,}</div></div>
      <div class="card"><div class="label">Est. Lost Revenue</div><div class="value">{money(ex["lost_revenue"])}</div></div>
    </div>
  </section>

  <section>
    <h2>Spend by Vendor</h2>
    {_rows_table(["Vendor", "Spend", "Share"], vendor_rows)}
  </section>

  <section>
    <h2>Spend by Channel</h2>
    {_rows_table(["Channel", "Spend", "Share"], channel_rows)}
  </section>

  <section>
    <h2>Spend by Region</h2>
    {_rows_table(["Region", "Spend", "Share"], region_rows)}
  </section>

  <section>
    <h2>Return on Ad Spend (by Vendor)</h2>
    {_rows_table(["Vendor", "Jobs", "Revenue", "Spend", "ROAS"], roas_rows)}
  </section>

  <footer>
    Marketing Performance Analysis for {esc(p.name)} · period {esc(meta["period"])} ·
    generated by the marketing-performance-report skill ·
    data mode: {esc(meta["data_mode"])}.
  </footer>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    a = argparse.ArgumentParser(description="Render the report HTML.")
    a.add_argument("--partner", required=True)
    a.add_argument("--period", required=True)
    a.add_argument("--spend-period", default=None)
    return a.parse_args()


def main() -> None:
    args = parse_args()
    rd = run_dir(args.partner, args.period)
    bundle = read_json(rd / "data.json")
    ex = read_json(rd / "section-executive.json")
    spend = read_json(rd / "section-spend.json")
    roas = read_json(rd / "section-roas.json")
    partner = get_partner(args.partner)

    out = rd / "marketing-analysis.html"
    out.write_text(build_html(partner, bundle["meta"], ex, spend, roas))
    print(f"Wrote {out}  ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

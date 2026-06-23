#!/usr/bin/env python3
"""
Warranty Jobs Report — database query script.

Connects to the warranty database, runs the jobs query for the requested
date range, and writes a JSON payload to stdout.

Usage:
    python3 query_warranty_jobs.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]

Environment variables (set these in your deployment environment):
    DB_HOST      Postgres host          (default: localhost)
    DB_PORT      Postgres port          (default: 5432)
    DB_NAME      Database name          (default: warranty_db)
    DB_USER      Database user          (default: warranty_reader)
    DB_PASSWORD  Database password      (required; no default)

When the environment is not yet wired up this script exits with a clear error
rather than silently returning empty results.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------------------
# Dependency check — psycopg2 is the only non-stdlib requirement
# ---------------------------------------------------------------------------
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print(
        "ERROR: psycopg2 is not installed. Run: pip install psycopg2-binary",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------

QUERY = """
SELECT
    wj.job_id,
    c.name                          AS customer,
    p.name                          AS product,
    wj.serial_number,
    wj.status,
    wj.priority,
    wj.filed_date,
    wj.last_updated,
    t.full_name                     AS technician,
    wj.description
FROM warranty_jobs        wj
JOIN customers            c  ON c.customer_id  = wj.customer_id
JOIN products             p  ON p.product_id   = wj.product_id
LEFT JOIN technicians     t  ON t.technician_id = wj.assigned_technician_id
WHERE wj.filed_date BETWEEN %(start_date)s AND %(end_date)s
ORDER BY
    CASE wj.priority
        WHEN 'high'   THEN 1
        WHEN 'medium' THEN 2
        WHEN 'low'    THEN 3
        ELSE               4
    END,
    wj.filed_date ASC;
"""

SUMMARY_QUERY = """
SELECT
    COUNT(*)                                        AS total,
    COUNT(*) FILTER (WHERE status = 'open')         AS open,
    COUNT(*) FILTER (WHERE status = 'in_progress')  AS in_progress,
    COUNT(*) FILTER (WHERE status = 'closed')       AS closed,
    COUNT(*) FILTER (WHERE status = 'rejected')     AS rejected
FROM warranty_jobs
WHERE filed_date BETWEEN %(start_date)s AND %(end_date)s;
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    today = date.today()
    parser = argparse.ArgumentParser(description="Query warranty jobs and emit JSON.")
    parser.add_argument(
        "--start-date",
        default=(today - timedelta(days=30)).isoformat(),
        help="Start of date range (YYYY-MM-DD). Defaults to 30 days ago.",
    )
    parser.add_argument(
        "--end-date",
        default=today.isoformat(),
        help="End of date range (YYYY-MM-DD). Defaults to today.",
    )
    return parser.parse_args()


def get_connection():
    """Build a psycopg2 connection from environment variables."""
    required = {"DB_PASSWORD"}
    missing = required - set(os.environ)
    if missing:
        print(
            f"ERROR: Missing required environment variable(s): {', '.join(sorted(missing))}",
            file=sys.stderr,
        )
        sys.exit(1)

    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "warranty_db"),
        user=os.getenv("DB_USER", "warranty_reader"),
        password=os.environ["DB_PASSWORD"],
        connect_timeout=10,
    )


def row_to_dict(row) -> dict:
    """Convert a psycopg2 RealDictRow to a plain dict with serialisable types."""
    out = dict(row)
    for key, value in out.items():
        if isinstance(value, (date, datetime)):
            out[key] = value.isoformat()
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()
    params = {"start_date": args.start_date, "end_date": args.end_date}

    try:
        conn = get_connection()
    except psycopg2.OperationalError as exc:
        print(f"ERROR: Could not connect to the database — {exc}", file=sys.stderr)
        sys.exit(1)

    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Summary counts
            cur.execute(SUMMARY_QUERY, params)
            summary_row = cur.fetchone()
            summary = {
                "total":       int(summary_row["total"]),
                "open":        int(summary_row["open"]),
                "in_progress": int(summary_row["in_progress"]),
                "closed":      int(summary_row["closed"]),
                "rejected":    int(summary_row["rejected"]),
            }

            # Full job list
            cur.execute(QUERY, params)
            jobs = [row_to_dict(r) for r in cur.fetchall()]

    conn.close()

    payload = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "period": {"start": args.start_date, "end": args.end_date},
        "summary": summary,
        "jobs": jobs,
    }

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

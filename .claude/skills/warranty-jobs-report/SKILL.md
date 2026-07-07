---
name: warranty-jobs-report
description: Generates a Warranty Jobs Report by querying a hypothetical warranty database for open, in-progress, and recently closed warranty jobs. Use when the user invokes /warranty-jobs-report or asks for a warranty jobs summary/report.
---

# warranty-jobs-report

Produces a structured Warranty Jobs Report by running a SQL query against the warranty database and formatting the results into a readable summary.

---

## Step 1 — Run the database query script

Execute the query script, passing the desired date range as arguments:

```bash
python3 .claude/skills/warranty-jobs-report/scripts/query_warranty_jobs.py \
  --start-date <YYYY-MM-DD> \
  --end-date <YYYY-MM-DD>
```

If no dates are supplied, the script defaults to the last 30 days relative to today.

The script prints a JSON payload to stdout with this shape:

```json
{
  "generated_at": "YYYY-MM-DD HH:MM:SS",
  "period": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" },
  "summary": {
    "total": 0,
    "open": 0,
    "in_progress": 0,
    "closed": 0,
    "rejected": 0
  },
  "jobs": [
    {
      "job_id": "WJ-00001",
      "customer": "Acme Corp",
      "product": "Industrial Pump Model X",
      "serial_number": "SN-99238",
      "status": "open",
      "priority": "high",
      "filed_date": "YYYY-MM-DD",
      "last_updated": "YYYY-MM-DD",
      "technician": null,
      "description": "Unit fails to prime after 30 minutes of operation."
    }
  ]
}
```

---

## Step 2 — Interpret the output

Parse the JSON returned by the script and build a plain-language report covering:

1. **Period** — the date range queried.
2. **Summary counts** — total, open, in-progress, closed, rejected.
3. **High-priority open jobs** — list any jobs with `priority == "high"` and `status == "open"`, including job ID, customer, product, and description.
4. **Overdue jobs** — list jobs where `last_updated` is more than 14 days before today and status is not `"closed"` or `"rejected"`.
5. **Recently closed** — list jobs closed within the period.

---

## Step 3 — Present the report

Format the report as a markdown table for the job list and a short paragraph for the summary. Example structure:

```
## Warranty Jobs Report — <start> to <end>

**Summary:** X total | X open | X in-progress | X closed | X rejected

### High-Priority Open Jobs
| Job ID   | Customer  | Product          | Filed      | Description              |
|----------|-----------|------------------|------------|--------------------------|
| WJ-00001 | Acme Corp | Industrial Pump  | 2026-05-01 | Unit fails to prime ...  |

### Overdue Jobs (no update > 14 days)
...

### Recently Closed
...
```

---

## Anti-patterns

- Do not fabricate job records — if the script returns an empty `jobs` array, report that no jobs matched the criteria.
- Do not modify the SQL in the script at runtime; query-tuning belongs in the script itself.
- Do not skip the summary section — counts give the reader the at-a-glance state without scanning the full table.

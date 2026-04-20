---
name: sage-intacct-reporter
description: Read-only reporting against Sage Intacct (GL, AP, AR, customers, vendors) via the XML Web Services API. Use when the user asks to pull Intacct data — last N transactions, vendor lists, bills, invoices, trial balances, AP/AR aging, chart of accounts, or any reconciliation against Sage Intacct. Credentials come from a k8s secret mounted on the job.
---

# sage-intacct-reporter

Read-only Sage Intacct client. **Do not run `pip install` or read the source to figure out what to do — use the prescriptive commands below.** The agent-worker image already has `python3` + `requests`, and `scripts/run_query.py` self-bootstraps its own `sys.path`.

## Quick start

```bash
cd /workspace/.claude/skills/sage-intacct-reporter
python3 scripts/run_query.py <command> [args]
```

Credentials (`INTACCT_*` env vars) are mounted automatically by the k8s secret
named in the caller's `secret_refs` or the platform default (`DEFAULT_AGENT_SECRET_REF`). No setup steps.

## Common queries — copy/paste, do not explore

| User asks for | Command | Notes |
|---|---|---|
| "test the connection" | `python3 scripts/run_query.py test` | Only does getAPISession. |
| **"last N transactions"** | `python3 scripts/run_query.py transactions --limit N` | **This is the right answer for any phrasing of "recent activity / journal / payments / transactions".** Merges AP bills + AR invoices, server-side orderby `WHENCREATED desc`. No date filter needed — just pass `--limit`. Use `--since MM/DD/YYYY` only if you want to bound the window. |
| "list active vendors" | `python3 scripts/run_query.py vendors --all` | Paginates. ~6K rows on typical tenant. |
| "list customers" | `python3 scripts/run_query.py customers --all` | |
| "AP bills since date" | `python3 scripts/run_query.py bills --since MM/DD/YYYY` | |
| "AR invoices since date" | `python3 scripts/run_query.py invoices --since MM/DD/YYYY` | |
| "chart of accounts" | `python3 scripts/run_query.py accounts` | |
| "what fields does X have" | `python3 scripts/run_query.py inspect OBJECT` | e.g. `inspect VENDOR`, `inspect APBILL`. |

All commands write JSON to stdout in the shape `{"total": N, "count": M, "records": [...]}` (`transactions` emits a flat array). Pipe to `python3 -c "import json, sys; ..."` to reshape into the table the user asked for.

## Known limitations — do not retry these

- **`GLENTRY` is NOT queryable via `readByQuery`** on this tenant (fails with `IntacctAPIError: DL02000001`). The `get_gl_entries()` helper in `queries.py` is kept only for tenants that have this access explicitly enabled — **do not call it**. For journal-like data, use `transactions` (AP + AR) or `GLBATCH` via `read_by_query("GLBATCH", ...)`.
- `WHENCREATED` is stored as `MM/DD/YYYY` string. The `transactions` helper parses it into a date tuple before sorting, so cross-year sorts work correctly.
- Every Intacct read requires an HTTP POST (yes, for reads — that's how their XML API works). No REST endpoint exists.

## When the canned commands aren't enough

Drop to Python directly. Same zero-install pattern — the bootstrap is already in `scripts/run_query.py`, reuse the import preamble:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("/workspace/.claude/skills/sage-intacct-reporter/src")))

from intacct.client import IntacctClient
c = IntacctClient()
result = c.read_by_query(
    "APBILL",
    query="WHENCREATED >= '04/01/2026'",
    fields="RECORDNO,WHENCREATED,VENDORNAME,TOTALENTERED,STATE",
    pagesize=100,
)
print(result.total_count, "bills,", len(result.records), "in this page")
```

Supported object families (for `inspect` or raw `read_by_query`): GL (`GLBATCH`, `GLACCOUNT`, `GLACCOUNTBALANCE`), AP (`APBILL`, `APBILLITEM`, `APPAYMENT`), AR (`ARINVOICE`, `ARINVOICEITEM`, `ARPAYMENT`), entities (`CUSTOMER`, `VENDOR`, `CONTACT`, `EMPLOYEE`), reference (`DEPARTMENT`, `LOCATION`, `CLASS`, `PROJECT`). `GLENTRY` is listed in the API docs but blocked on this tenant — see "Known limitations".

## Errors

- `IntacctAPIError(error_code=...)` — API returned a failure. Report `error_code` to the user; do not guess how to work around it.
- `KeyError: Missing env var INTACCT_...` — credentials not mounted. Tell the user to pass `secret_refs` on `start_session`, or confirm `DEFAULT_AGENT_SECRET_REF` is set on the agent-server.

## Output convention

Write deliverables (CSV, JSON, markdown tables) to `/workspace/` (the git-synced workspace root) — **not** into `.claude/skills/`.

## Operator notes — creating a k8s secret

```bash
kubectl create secret generic intacct-credentials-<tenant> \
  --namespace=shiftagent \
  --from-literal=INTACCT_SENDER_ID=... \
  --from-literal=INTACCT_SENDER_PASSWORD=... \
  --from-literal=INTACCT_COMPANY_ID=... \
  --from-literal=INTACCT_USER_ID=... \
  --from-literal=INTACCT_USER_PASSWORD=...
```

MCP caller then selects it via `start_session { "secret_refs": ["intacct-credentials-<tenant>"] }`. Omit `secret_refs` to use the platform default.

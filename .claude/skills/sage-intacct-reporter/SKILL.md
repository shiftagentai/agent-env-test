---
name: sage-intacct-reporter
description: Read-only reporting against Sage Intacct (GL, AP, AR, customers, vendors) via the XML Web Services API. Use when the user asks to pull Intacct data — vendor lists, bills, invoices, trial balances, GL entries, AP/AR aging, chart of accounts, last N transactions, or any reconciliation against Sage Intacct. Credentials come from a k8s secret mounted on the job.
---

# sage-intacct-reporter

Read-only Sage Intacct client. Session auth → `readByQuery` / `read` / `readMore` / `inspect`.

**Zero setup required.** The agent-worker image already has `python3` and `requests` baked in, and the skill's `scripts/run_query.py` self-bootstraps its own `sys.path`. **Do not run `pip install` or `uv pip install`** — just run the script.

## Required env vars

Injected automatically by the k8s secret the agent-server mounts via `envFrom`
(selected per-session through `secret_refs` on `start_session`, or by the
platform default `DEFAULT_AGENT_SECRET_REF`).

- `INTACCT_SENDER_ID`
- `INTACCT_SENDER_PASSWORD`
- `INTACCT_COMPANY_ID`
- `INTACCT_USER_ID`
- `INTACCT_USER_PASSWORD`

If any are missing, the client raises `KeyError` with a clear message.
Surface the error to the user — do not guess values.

## Usage

Run directly from the skill directory — no install step.

```bash
cd /workspace/.claude/skills/sage-intacct-reporter

# Smoke test — only does getAPISession
python3 scripts/run_query.py test

# Query helpers
python3 scripts/run_query.py vendors --all
python3 scripts/run_query.py bills --since 01/01/2025 --all
python3 scripts/run_query.py invoices --since 01/01/2025
python3 scripts/run_query.py accounts
python3 scripts/run_query.py inspect VENDOR
```

From Python (also zero-install — add `src/` to `sys.path` the same way
`run_query.py` does, or just run scripts from inside the skill dir):

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("/workspace/.claude/skills/sage-intacct-reporter/src")))

from intacct.client import IntacctClient
from intacct.queries import get_vendors, get_bills, get_gl_entries

c = IntacctClient()
vendors = get_vendors(c, active_only=True, auto_paginate=True)
bills   = get_bills(c, since_date="01/01/2025", auto_paginate=True)
entries = get_gl_entries(c, pagesize=10)   # last 10 GL entries
```

## "Last N transactions" recipe

Intacct has no single `transactions` object. Transactions live in per-ledger
tables. The typical meaning is **GL journal entries** — use `GLENTRY`:

```bash
cd /workspace/.claude/skills/sage-intacct-reporter
python3 -c "
import sys; sys.path.insert(0, 'src')
from intacct.client import IntacctClient
from intacct.queries import get_gl_entries
c = IntacctClient()
r = get_gl_entries(c, pagesize=10)
print(f'Showing {len(r.records)} of {r.total_count} GL entries')
for rec in r.records:
    print(rec)
"
```

If the user really wants AP bills or AR invoices instead, swap to
`get_bills(c, since_date=..., pagesize=10)` or `get_invoices(...)`.

## Supported Object Families

| Category | Objects |
|---|---|
| GL | `GLENTRY`, `GLBATCH`, `GLACCOUNT`, `GLACCOUNTBALANCE` |
| AP | `APBILL`, `APBILLITEM`, `APPAYMENT` |
| AR | `ARINVOICE`, `ARINVOICEITEM`, `ARPAYMENT` |
| Entities | `CUSTOMER`, `VENDOR`, `CONTACT`, `EMPLOYEE` |
| Reference | `DEPARTMENT`, `LOCATION`, `CLASS`, `PROJECT` |

Helpers in `src/intacct/queries.py` wrap the common queries. Drop to
`IntacctClient.read_by_query(object_type, query, fields)` for custom ones.

## Errors

- `IntacctAPIError` with `error_code`. Auto-retries once on session expiry
  (`XL03000006`).
- `KeyError` from `intacct.secrets` — credentials missing. Fix the k8s
  secret or the `secret_refs` passed to `start_session`.

## Output

Write deliverables (CSV, JSON, markdown reports) to the working directory
(`/workspace/...`), **not** under `.claude/skills/`.

## Operator Notes — Creating a K8s Secret

```bash
kubectl create secret generic intacct-credentials-acme \
  --namespace=shiftagent \
  --from-literal=INTACCT_SENDER_ID=... \
  --from-literal=INTACCT_SENDER_PASSWORD=... \
  --from-literal=INTACCT_COMPANY_ID=... \
  --from-literal=INTACCT_USER_ID=... \
  --from-literal=INTACCT_USER_PASSWORD=...
```

MCP caller then selects it:

```jsonc
{
  "profile_id": "...",
  "prompt": "...",
  "secret_refs": ["intacct-credentials-acme"]
}
```

If `secret_refs` is omitted, the agent-server falls back to the secret
named in `DEFAULT_AGENT_SECRET_REF` (set on the agent-server deployment).

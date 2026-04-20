---
name: sage-intacct-reporter
description: Read-only reporting against Sage Intacct (GL, AP, AR, customers, vendors) via the XML Web Services API. Use when the user asks to pull Intacct data — vendor lists, bills, invoices, trial balances, GL entries, AP/AR aging, chart of accounts, or any reconciliation against Sage Intacct. Requires a k8s secret with Intacct sender/user/company credentials mounted on the job.
---

# sage-intacct-reporter

Read-only Sage Intacct client. Session auth → `readByQuery` / `read` / `readMore` / `inspect`.

## Setup (once per job)

The skill directory is git-synced into `/workspace/.claude/skills/sage-intacct-reporter`.

```bash
cd /workspace/.claude/skills/sage-intacct-reporter
uv pip install --system -e .     # installs `requests` and the local `intacct` package
```

## Required env vars

These are injected by a k8s secret the caller selected via `secret_refs` on
`start_session`, or by a default secret configured on the agent-server
(`DEFAULT_AGENT_SECRET_REF`).

- `INTACCT_SENDER_ID`
- `INTACCT_SENDER_PASSWORD`
- `INTACCT_COMPANY_ID`
- `INTACCT_USER_ID`
- `INTACCT_USER_PASSWORD`

If any are missing, the client raises `KeyError` with a clear message. Do not
guess values; surface the error to the user.

## Usage

```bash
# Quickest smoke test
python scripts/run_query.py test

# Common queries
python scripts/run_query.py vendors --all
python scripts/run_query.py bills --since 01/01/2025 --all
python scripts/run_query.py accounts
python scripts/run_query.py inspect VENDOR
```

Or from Python:

```python
from intacct.client import IntacctClient
from intacct.queries import get_vendors, get_bills, get_gl_entries

c = IntacctClient()
vendors = get_vendors(c, active_only=True, auto_paginate=True)
bills   = get_bills(c, since_date="01/01/2025", auto_paginate=True)
```

## Supported Object Families

| Category | Objects |
|---|---|
| GL | `GLENTRY`, `GLBATCH`, `GLACCOUNT`, `GLACCOUNTBALANCE` |
| AP | `APBILL`, `APBILLITEM`, `APPAYMENT` |
| AR | `ARINVOICE`, `ARINVOICEITEM`, `ARPAYMENT` |
| Entities | `CUSTOMER`, `VENDOR`, `CONTACT`, `EMPLOYEE` |
| Reference | `DEPARTMENT`, `LOCATION`, `CLASS`, `PROJECT` |

Helpers in `src/intacct/queries.py` wrap the common queries with sensible field
lists. Drop down to `IntacctClient.read_by_query(object_type, query, fields)`
for anything custom.

## Errors

- `IntacctAPIError` with `error_code`. The client auto-retries once on session
  expiry (`XL03000006`).
- `KeyError` from `intacct.secrets` — credentials missing. Fix the k8s secret
  or the `secret_refs` passed to start_session.

## Output

Write deliverables (CSV, JSON, markdown reports) to the working directory
(`/workspace/...`), **not** under `.claude/skills/`.

## Operator Notes — Creating a K8s Secret

```bash
kubectl create secret generic intacct-credentials-acme \
  --namespace=default \
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

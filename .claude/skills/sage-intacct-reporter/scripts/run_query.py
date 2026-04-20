#!/usr/bin/env python3
"""Thin CLI for running canned Intacct queries.

Usage:
  python scripts/run_query.py test
  python scripts/run_query.py vendors [--since MM/DD/YYYY] [--all]
  python scripts/run_query.py customers [--all]
  python scripts/run_query.py bills --since MM/DD/YYYY
  python scripts/run_query.py invoices --since MM/DD/YYYY
  python scripts/run_query.py accounts
  python scripts/run_query.py inspect OBJECT

Credentials come from env vars (INTACCT_SENDER_ID etc.), injected by the k8s
secret mounted on the agent container.
"""

import argparse
import json
import sys
from pathlib import Path

# Zero-install bootstrap: put the bundled `src/` on sys.path so `intacct.*`
# imports work without `pip install -e .`. The `requests` dep is baked into
# the agent-worker image.
_SKILL_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SKILL_SRC) not in sys.path:
    sys.path.insert(0, str(_SKILL_SRC))

from intacct.client import IntacctAPIError, IntacctClient
from intacct.queries import (
    get_accounts,
    get_bills,
    get_customers,
    get_invoices,
    get_recent_transactions,
    get_vendors,
)

COMMANDS = {
    "test": "Validate credentials and establish a session",
    "transactions": "Last N transactions (AP bills + AR invoices merged, sorted by WHENCREATED desc)",
    "vendors": "List vendors (--all for paginated, --since MM/DD/YYYY ignored)",
    "customers": "List customers",
    "bills": "AP bills since a given date",
    "invoices": "AR invoices since a given date",
    "accounts": "GL chart of accounts",
    "inspect": "Dump field metadata for an object type",
}


def _dump(records, total=None):
    print(json.dumps({"total": total, "count": len(records), "records": records}, indent=2, default=str))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=COMMANDS.keys())
    parser.add_argument("object_type", nargs="?", help="For `inspect`: Intacct object name")
    parser.add_argument("--since", help="MM/DD/YYYY filter for bills/invoices/transactions")
    parser.add_argument("--limit", type=int, default=10, help="Row cap for `transactions` (default 10)")
    parser.add_argument("--all", action="store_true", help="Auto-paginate through all results")
    args = parser.parse_args()

    try:
        client = IntacctClient()

        if args.command == "test":
            print(json.dumps(client.test_connection()))
            return 0

        if args.command == "transactions":
            rows = get_recent_transactions(
                client, limit=args.limit, since_date=args.since,
            )
            _dump(rows)
            return 0

        if args.command == "vendors":
            qr = get_vendors(client, auto_paginate=args.all)
            _dump(qr.records, qr.total_count)
            return 0

        if args.command == "customers":
            qr = get_customers(client, auto_paginate=args.all)
            _dump(qr.records, qr.total_count)
            return 0

        if args.command == "bills":
            if not args.since:
                print("--since MM/DD/YYYY is required for bills", file=sys.stderr)
                return 2
            qr = get_bills(client, since_date=args.since, auto_paginate=args.all)
            _dump(qr.records, qr.total_count)
            return 0

        if args.command == "invoices":
            if not args.since:
                print("--since MM/DD/YYYY is required for invoices", file=sys.stderr)
                return 2
            qr = get_invoices(client, since_date=args.since, auto_paginate=args.all)
            _dump(qr.records, qr.total_count)
            return 0

        if args.command == "accounts":
            qr = get_accounts(client, auto_paginate=args.all)
            _dump(qr.records, qr.total_count)
            return 0

        if args.command == "inspect":
            if not args.object_type:
                print("`inspect` requires an object_type (e.g. VENDOR)", file=sys.stderr)
                return 2
            fields = client.inspect(args.object_type, detail=True)
            _dump(fields)
            return 0

    except IntacctAPIError as e:
        print(f"Intacct API error ({e.error_code}): {e}", file=sys.stderr)
        return 1
    except KeyError as e:
        print(str(e), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

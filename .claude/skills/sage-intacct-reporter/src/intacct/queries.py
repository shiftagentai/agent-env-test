"""Pre-built queries for common Intacct objects."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from intacct.client import IntacctClient, QueryResult


# ---------------------------------------------------------------------------
# Recent transactions (AP bills + AR invoices merged)
# ---------------------------------------------------------------------------

def get_recent_transactions(
    client: IntacctClient,
    *,
    limit: int = 10,
    since_date: str | None = None,
) -> list[dict]:
    """Merge AP bills + AR invoices, sort by WHENCREATED desc, return top `limit`.

    Intacct has no single `transactions` object and `GLENTRY` is not queryable
    via readByQuery on most tenants (fails with `DL02000001`). The practical
    "recent transactions" view is AP bills + AR invoices combined.

    Args:
        limit: Maximum number of rows to return.
        since_date: Optional MM/DD/YYYY lower bound on WHENCREATED. If omitted,
                    returns the most recent N across all time — Intacct sorts
                    server-side by WHENCREATED desc before pagesize truncates.

    Returns:
        List of dicts with normalized fields: ``type`` ("AP Bill" | "AR Invoice"),
        ``party`` (vendor or customer name), plus the raw record fields.
    """
    # WHENCREATED is MM/DD/YYYY string; parsed tuple for correct cross-year sort.
    def _sort_key(r: dict) -> tuple[int, int, int]:
        s = r.get("WHENCREATED") or ""
        try:
            mm, dd, yyyy = s.split("/")
            return (int(yyyy), int(mm), int(dd))
        except ValueError:
            return (0, 0, 0)

    ap_fields = "RECORDNO,WHENCREATED,VENDORNAME,DESCRIPTION,TOTALENTERED,TOTALDUE,TOTALPAID,STATE"
    ar_fields = "RECORDNO,WHENCREATED,CUSTOMERNAME,DESCRIPTION,TOTALENTERED,TOTALDUE,TOTALPAID,STATE"

    # readByQuery has no server-side sort and pagesize truncates against storage
    # (creation) order. For "most recent N", we need a window small enough that
    # ALL matching rows fit in one page (total_count <= pagesize) — then a
    # client-side sort gives the correct top-N. Widen until we have `limit`
    # rows AND both result sets are complete.
    PAGESIZE = 2000  # Intacct max
    candidate_days = [1, 7, 30, 90, 365, 1825]
    if since_date is not None:
        windows: list[str | None] = [since_date]
    else:
        windows = [(date.today() - timedelta(days=d)).strftime("%m/%d/%Y")
                   for d in candidate_days]
        windows.append(None)  # final fallback: no filter at all

    rows: list[dict] = []
    last_ap_total = 0
    last_ar_total = 0
    for lower in windows:
        q = f"WHENCREATED >= '{lower}'" if lower else ""
        ap = client.read_by_query("APBILL",    query=q, fields=ap_fields, pagesize=PAGESIZE)
        ar = client.read_by_query("ARINVOICE", query=q, fields=ar_fields, pagesize=PAGESIZE)
        last_ap_total, last_ar_total = ap.total_count, ar.total_count

        # If the window is too wide (either side truncated), the newest rows may
        # not be in this page — stop widening here. Use the previous successful
        # iteration's rows if we had any.
        if ap.total_count > PAGESIZE or ar.total_count > PAGESIZE:
            break

        rows = []
        for r in ap.records:
            rows.append({"type": "AP Bill",    "party": r.get("VENDORNAME"),   **r})
        for r in ar.records:
            rows.append({"type": "AR Invoice", "party": r.get("CUSTOMERNAME"), **r})
        rows.sort(key=_sort_key, reverse=True)

        if len(rows) >= limit:
            break

    if not rows and (last_ap_total > PAGESIZE or last_ar_total > PAGESIZE):
        # First window already too wide — the tenant is extremely dense. Surface
        # a clear error so the caller narrows explicitly.
        raise RuntimeError(
            f"Tenant too dense for recent-transactions heuristic "
            f"(AP total={last_ap_total}, AR total={last_ar_total}, pagesize={PAGESIZE}). "
            f"Pass an explicit `since_date` narrow enough that each side has "
            f"\u2264 {PAGESIZE} matching rows."
        )

    return rows[:limit]


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

def get_customers(
    client: IntacctClient,
    *,
    active_only: bool = True,
    fields: str = "CUSTOMERID,NAME,STATUS,DISPLAYCONTACT.EMAIL1,DISPLAYCONTACT.PHONE1",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query customer records."""
    query = "STATUS = 'T'" if active_only else ""
    return client.read_by_query(
        "CUSTOMER", query=query, fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_customer_by_id(client: IntacctClient, customer_id: str) -> list[dict]:
    """Look up a single customer by CUSTOMERID."""
    qr = client.read_by_query("CUSTOMER", query=f"CUSTOMERID = '{customer_id}'", pagesize=1)
    return qr.records


# ---------------------------------------------------------------------------
# Vendors
# ---------------------------------------------------------------------------

def get_vendors(
    client: IntacctClient,
    *,
    active_only: bool = True,
    fields: str = "VENDORID,NAME,STATUS,DISPLAYCONTACT.EMAIL1,DISPLAYCONTACT.PHONE1",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query vendor records."""
    query = "STATUS = 'T'" if active_only else ""
    return client.read_by_query(
        "VENDOR", query=query, fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_active_vendors(
    client: IntacctClient,
    *,
    pagesize: int = 1000,
) -> QueryResult:
    """Fetch all active vendors with all fields."""
    return client.read_by_query(
        "VENDOR", query="STATUS = 'T'", fields="*", pagesize=pagesize, auto_paginate=True,
    )


def get_vendor_by_id(client: IntacctClient, vendor_id: str) -> list[dict]:
    """Look up a single vendor by VENDORID."""
    qr = client.read_by_query("VENDOR", query=f"VENDORID = '{vendor_id}'", pagesize=1)
    return qr.records


# ---------------------------------------------------------------------------
# AR — Invoices & Payments
# ---------------------------------------------------------------------------

def get_invoices(
    client: IntacctClient,
    *,
    since_date: str | None = None,
    fields: str = "RECORDNO,RECORDID,CUSTOMERID,CUSTOMERNAME,TOTALDUE,TOTALPAID,TOTALENTERED,WHENCREATED,WHENDUE,STATE",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query AR invoices, optionally filtered by creation date.

    Args:
        since_date: Filter invoices created on or after this date (MM/DD/YYYY).
    """
    query = f"WHENCREATED >= '{since_date}'" if since_date else ""
    return client.read_by_query(
        "ARINVOICE", query=query, fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_invoice_items(
    client: IntacctClient,
    *,
    invoice_recordno: str | None = None,
    fields: str = "RECORDNO,RECORDKEY,ACCOUNTNO,ACCOUNTTITLE,AMOUNT,DEPARTMENTID,LOCATIONID",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query AR invoice line items, optionally for a specific invoice."""
    query = f"RECORDKEY = '{invoice_recordno}'" if invoice_recordno else ""
    return client.read_by_query(
        "ARINVOICEITEM", query=query, fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_ar_payments(
    client: IntacctClient,
    *,
    since_date: str | None = None,
    fields: str = "RECORDNO,CUSTOMERID,CUSTOMERNAME,PAYMENTTYPE,PAYMENTDATE,TOTALENTERED,TOTALPAID,STATE,WHENCREATED",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query AR payments."""
    query = f"WHENCREATED >= '{since_date}'" if since_date else ""
    return client.read_by_query(
        "ARPAYMENT", query=query, fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


# ---------------------------------------------------------------------------
# AP — Bills & Payments
# ---------------------------------------------------------------------------

def get_bills(
    client: IntacctClient,
    *,
    since_date: str | None = None,
    fields: str = "RECORDNO,RECORDID,VENDORID,VENDORNAME,TOTALDUE,TOTALPAID,TOTALENTERED,WHENCREATED,WHENDUE,STATE",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query AP bills, optionally filtered by creation date.

    Args:
        since_date: Filter bills created on or after this date (MM/DD/YYYY).
    """
    query = f"WHENCREATED >= '{since_date}'" if since_date else ""
    return client.read_by_query(
        "APBILL", query=query, fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_bill_items(
    client: IntacctClient,
    *,
    bill_recordno: str | None = None,
    fields: str = "RECORDNO,RECORDKEY,ACCOUNTNO,ACCOUNTTITLE,AMOUNT,DEPARTMENTID,LOCATIONID",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query AP bill line items, optionally for a specific bill."""
    query = f"RECORDKEY = '{bill_recordno}'" if bill_recordno else ""
    return client.read_by_query(
        "APBILLITEM", query=query, fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_ap_payments(
    client: IntacctClient,
    *,
    since_date: str | None = None,
    fields: str = "RECORDNO,VENDORID,VENDORNAME,PAYMENTTYPE,PAYMENTDATE,TOTALENTERED,TOTALPAID,STATE,WHENCREATED",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query AP payments."""
    query = f"WHENCREATED >= '{since_date}'" if since_date else ""
    return client.read_by_query(
        "APPAYMENT", query=query, fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


# ---------------------------------------------------------------------------
# GL — Accounts, Entries, Batches, Balances
# ---------------------------------------------------------------------------

def get_accounts(
    client: IntacctClient,
    *,
    fields: str = "ACCOUNTNO,TITLE,ACCOUNTTYPE,NORMALBALANCE,STATUS",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query all GL accounts (chart of accounts)."""
    return client.read_by_query(
        "GLACCOUNT", fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_gl_entries(
    client: IntacctClient,
    *,
    since_date: str | None = None,
    fields: str = "RECORDNO,BATCH_DATE,ACCOUNTNO,ACCOUNTTITLE,DEBIT,CREDIT,AMOUNT,DEPARTMENTID,LOCATIONID,DESCRIPTION",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query GL journal entries — NOT SUPPORTED on most Intacct tenants.

    WARNING: `readByQuery` against `GLENTRY` typically fails with
    `IntacctAPIError: DL02000001`. This helper is kept only for tenants that
    have `GLENTRY` query access explicitly enabled. For a working journal-like
    view, use `get_recent_transactions()` (AP bills + AR invoices) or
    `get_gl_batches()` (batch headers).

    Args:
        since_date: Filter entries with BATCH_DATE on or after this date (MM/DD/YYYY).
    """
    query = f"BATCH_DATE >= '{since_date}'" if since_date else ""
    return client.read_by_query(
        "GLENTRY", query=query, fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_gl_batches(
    client: IntacctClient,
    *,
    since_date: str | None = None,
    fields: str = "RECORDNO,BATCH_DATE,BATCH_TITLE,JOURNAL,STATE",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query GL journal batches."""
    query = f"BATCH_DATE >= '{since_date}'" if since_date else ""
    return client.read_by_query(
        "GLBATCH", query=query, fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_account_balances(
    client: IntacctClient,
    *,
    reporting_period: str | None = None,
    fields: str = "ACCOUNTNO,ACCOUNTTITLE,DEPARTMENTID,LOCATIONID,TOTALDEBIT,TOTALCREDIT,ENDBALANCE,REPORTINGPERIODNAME",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query GL account balances, optionally for a specific reporting period."""
    query = f"REPORTINGPERIODNAME = '{reporting_period}'" if reporting_period else ""
    return client.read_by_query(
        "GLACCOUNTBALANCE", query=query, fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


# ---------------------------------------------------------------------------
# Reference — Departments, Locations, Classes, Projects, Contacts, Employees
# ---------------------------------------------------------------------------

def get_departments(
    client: IntacctClient,
    *,
    fields: str = "DEPARTMENTID,TITLE,STATUS,PARENTID",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query departments."""
    return client.read_by_query(
        "DEPARTMENT", fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_locations(
    client: IntacctClient,
    *,
    fields: str = "LOCATIONID,NAME,STATUS,PARENTID",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query locations (entities)."""
    return client.read_by_query(
        "LOCATION", fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_classes(
    client: IntacctClient,
    *,
    fields: str = "CLASSID,NAME,STATUS,PARENTID",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query classes."""
    return client.read_by_query(
        "CLASS", fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_projects(
    client: IntacctClient,
    *,
    active_only: bool = True,
    fields: str = "PROJECTID,NAME,STATUS,CUSTOMERID,DEPARTMENTID",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query projects."""
    query = "STATUS = 'T'" if active_only else ""
    return client.read_by_query(
        "PROJECT", query=query, fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_employees(
    client: IntacctClient,
    *,
    active_only: bool = True,
    fields: str = "EMPLOYEEID,PERSONALINFO.CONTACTNAME,DEPARTMENTID,LOCATIONID,STATUS",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query employees."""
    query = "STATUS = 'T'" if active_only else ""
    return client.read_by_query(
        "EMPLOYEE", query=query, fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )


def get_contacts(
    client: IntacctClient,
    *,
    fields: str = "RECORDNO,CONTACTNAME,COMPANYNAME,EMAIL1,PHONE1",
    pagesize: int = 100,
    auto_paginate: bool = False,
) -> QueryResult:
    """Query contacts."""
    return client.read_by_query(
        "CONTACT", fields=fields, pagesize=pagesize, auto_paginate=auto_paginate,
    )

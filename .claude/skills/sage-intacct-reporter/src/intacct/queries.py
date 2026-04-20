"""Pre-built queries for common Intacct objects."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from intacct.client import IntacctClient, QueryResult


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
    """Query GL journal entries, optionally filtered by batch date.

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

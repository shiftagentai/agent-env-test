"""Sage Intacct XML API client — read-only operations."""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import requests

from intacct.secrets import get_secret

API_URL = "https://api.intacct.com/ia/xml/xmlgw.phtml"
DTD_VERSION = "3.0"
SESSION_EXPIRED_CODE = "XL03000006"


@dataclass
class QueryResult:
    """Result from read_by_query with pagination metadata."""

    records: list[dict] = field(default_factory=list)
    total_count: int = 0
    num_remaining: int = 0
    result_id: str = ""


class IntacctAPIError(Exception):
    """Raised when the Intacct API returns an error response."""

    def __init__(self, message: str, error_code: str = ""):
        super().__init__(message)
        self.error_code = error_code


class IntacctClient:
    """Read-only client for the Sage Intacct XML Web Services API."""

    def __init__(self) -> None:
        self._sender_id = get_secret("sender_id")
        self._sender_password = get_secret("sender_password")
        self._company_id = get_secret("company_id")
        self._user_id = get_secret("user_id")
        self._user_password = get_secret("user_password")
        self._session_id: str | None = None
        self._session = requests.Session()
        self._session.headers["Content-Type"] = "application/xml"

    # --- Public API ---

    def test_connection(self) -> dict:
        """Validate credentials by establishing a session. Returns session info."""
        self._get_session()
        return {"status": "ok", "session_id": self._session_id}

    def read_by_query(
        self,
        object_type: str,
        query: str = "",
        fields: str = "*",
        pagesize: int = 100,
        auto_paginate: bool = False,
        orderby: list[tuple[str, str]] | None = None,
    ) -> QueryResult:
        """Query Intacct objects.

        Args:
            object_type: Intacct object name (e.g. "VENDOR", "CUSTOMER").
            query: Intacct query filter (e.g. "STATUS = 'active'").
            fields: Comma-separated field list or "*" for all.
            pagesize: Records per page (max 2000).
            auto_paginate: If True, follows readMore until all records fetched.
                           Defaults to False (single page).
            orderby: Optional server-side sort as a list of ``(field, direction)``
                     tuples where direction is ``"ascending"`` or ``"descending"``.
                     Intacct does not sort by default — pagesize truncates against
                     storage order — so this is required when you want the most
                     recent N records via a single page.

        Returns:
            QueryResult with records and pagination metadata.
        """
        orderby_xml = ""
        if orderby:
            orders = "".join(
                f"<order><field>{field}</field><{direction}/></order>"
                for field, direction in orderby
            )
            orderby_xml = f"<orderby>{orders}</orderby>"

        function_xml = (
            f"<readByQuery>"
            f"<object>{object_type}</object>"
            f"<query>{query}</query>"
            f"<fields>{fields}</fields>"
            f"{orderby_xml}"
            f"<pagesize>{pagesize}</pagesize>"
            f"</readByQuery>"
        )
        result = self._call(function_xml)
        records = self._extract_records(result)
        data_elem = result.find(".//data")
        total_count = int(data_elem.get("totalcount", "0")) if data_elem is not None else 0
        num_remaining = int(data_elem.get("numremaining", "0")) if data_elem is not None else 0
        result_id = data_elem.get("resultId", "") if data_elem is not None else ""

        if auto_paginate:
            while num_remaining > 0 and result_id:
                more_result = self._read_more(result_id)
                records.extend(self._extract_records(more_result))
                attr = more_result.find(".//data")
                if attr is not None:
                    num_remaining = int(attr.get("numremaining", "0"))
                    result_id = attr.get("resultId", "")
                else:
                    break

        return QueryResult(
            records=records,
            total_count=total_count,
            num_remaining=num_remaining,
            result_id=result_id,
        )

    def read(self, object_type: str, keys: list[str], fields: str = "*") -> list[dict]:
        """Read specific records by key."""
        keys_str = ",".join(keys)
        function_xml = (
            f"<read>"
            f"<object>{object_type}</object>"
            f"<keys>{keys_str}</keys>"
            f"<fields>{fields}</fields>"
            f"</read>"
        )
        result = self._call(function_xml)
        return self._extract_records(result)

    def read_more(self, result_id: str) -> list[dict]:
        """Fetch the next page of a paginated result set."""
        return self._extract_records(self._read_more(result_id))

    def inspect(self, object_type: str, *, detail: bool = False) -> list[dict]:
        """Get field metadata for an object type.

        Args:
            object_type: Intacct object name.
            detail: If True, returns full metadata per field (type, required, etc.).
                    If False, returns just field names.

        Returns:
            List of dicts. Each has at least a "Name" key.
            With detail=True, includes DisplayLabel, Description, isRequired, etc.
        """
        detail_attr = ' detail="1"' if detail else ""
        function_xml = f"<inspect{detail_attr}><object>{object_type}</object></inspect>"
        result = self._call(function_xml)
        fields: list[dict] = []
        for field_el in result.iter("Field"):
            if len(field_el) > 0:
                fields.append(self._element_to_dict(field_el))
            else:
                fields.append({"Name": field_el.text})
        return fields

    # --- Session management ---

    def _get_session(self) -> str:
        """Get or create an API session. Returns the session ID."""
        if self._session_id is not None:
            return self._session_id

        request_xml = self._build_session_request()
        response = self._session.post(API_URL, data=request_xml)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        self._check_for_errors(root)

        session_id = root.findtext(".//sessionid")
        if not session_id:
            raise IntacctAPIError("No session ID in getAPISession response")
        self._session_id = session_id
        return self._session_id

    def _build_session_request(self) -> str:
        """Build the XML envelope for getAPISession with login credentials."""
        control_id = str(uuid.uuid4())
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<request>"
            "<control>"
            f"<senderid>{self._sender_id}</senderid>"
            f"<password>{self._sender_password}</password>"
            f"<controlid>{control_id}</controlid>"
            "<uniqueid>false</uniqueid>"
            f"<dtdversion>{DTD_VERSION}</dtdversion>"
            "<includewhitespace>false</includewhitespace>"
            "</control>"
            "<operation>"
            "<authentication>"
            "<login>"
            f"<userid>{self._user_id}</userid>"
            f"<companyid>{self._company_id}</companyid>"
            f"<password>{self._user_password}</password>"
            "</login>"
            "</authentication>"
            "<content>"
            f'<function controlid="{control_id}">'
            "<getAPISession/>"
            "</function>"
            "</content>"
            "</operation>"
            "</request>"
        )

    # --- Request building and sending ---

    def _build_request(self, function_xml: str) -> str:
        """Build an XML request envelope using the current session ID."""
        session_id = self._get_session()
        control_id = str(uuid.uuid4())
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<request>"
            "<control>"
            f"<senderid>{self._sender_id}</senderid>"
            f"<password>{self._sender_password}</password>"
            f"<controlid>{control_id}</controlid>"
            "<uniqueid>false</uniqueid>"
            f"<dtdversion>{DTD_VERSION}</dtdversion>"
            "<includewhitespace>false</includewhitespace>"
            "</control>"
            "<operation>"
            "<authentication>"
            f"<sessionid>{session_id}</sessionid>"
            "</authentication>"
            "<content>"
            f'<function controlid="{control_id}">'
            f"{function_xml}"
            "</function>"
            "</content>"
            "</operation>"
            "</request>"
        )

    def _send(self, xml_body: str) -> ET.Element:
        """POST XML to the Intacct API and return parsed response root."""
        response = self._session.post(API_URL, data=xml_body)
        response.raise_for_status()
        return ET.fromstring(response.text)

    def _call(self, function_xml: str, *, _retried: bool = False) -> ET.Element:
        """Build, send, and parse an API call. Retries once on session expiry."""
        xml_body = self._build_request(function_xml)
        root = self._send(xml_body)
        try:
            self._check_for_errors(root)
        except IntacctAPIError as e:
            if e.error_code == SESSION_EXPIRED_CODE and not _retried:
                self._session_id = None
                return self._call(function_xml, _retried=True)
            raise
        return root

    # --- Response parsing ---

    @staticmethod
    def _check_for_errors(root: ET.Element) -> None:
        """Check for API errors in the response and raise IntacctAPIError if found."""
        # Check operation-level result status
        for result in root.iter("result"):
            status = result.findtext("status")
            if status == "failure":
                error = result.find(".//error")
                if error is not None:
                    errno = error.findtext("errorno", "")
                    description = error.findtext("description2", "")
                    if not description:
                        description = error.findtext("description", "")
                    raise IntacctAPIError(description, error_code=errno)
                raise IntacctAPIError("Unknown API error")

        # Check control-level errors
        status = root.findtext(".//control/status")
        if status == "failure":
            errno = root.findtext(".//errormessage/error/errorno", "")
            description = root.findtext(".//errormessage/error/description2", "")
            if not description:
                description = root.findtext(".//errormessage/error/description", "")
            raise IntacctAPIError(description or "Control block failure", error_code=errno)

    @staticmethod
    def _extract_records(root: ET.Element) -> list[dict]:
        """Extract data records from an API response into a list of dicts."""
        records = []
        data = root.find(".//data")
        if data is None:
            return records
        for child in data:
            records.append(IntacctClient._element_to_dict(child))
        return records

    @staticmethod
    def _element_to_dict(element: ET.Element) -> dict:
        """Convert an XML element to a dict. Nested elements become nested dicts."""
        result: dict = {}
        for child in element:
            if len(child) > 0:
                result[child.tag] = IntacctClient._element_to_dict(child)
            else:
                result[child.tag] = child.text
        return result

    # --- Pagination ---

    def _read_more(self, result_id: str) -> ET.Element:
        """Fetch the next page of results."""
        function_xml = f"<readMore><resultId>{result_id}</resultId></readMore>"
        return self._call(function_xml)

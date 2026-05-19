import json
import os
import re
from typing import Optional

from .schemas import Invoice, LineItem, Party, PaymentDetails

INVOICE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "document_type": {
            "type": "string",
            "enum": ["invoice", "claim_form", "other"],
            "description": "Classify the document. Use claim_form if it contains "
            "policy number, incident, or insurance claim language.",
        },
        "invoice_number": {"type": ["string", "null"]},
        "policy_number": {"type": ["string", "null"], "description": "Insurance policy number, only set for claim_form documents"},
        "incident_date": {"type": ["string", "null"], "description": "ISO YYYY-MM-DD, only set for claim_form documents"},
        "issue_date": {"type": ["string", "null"], "description": "ISO YYYY-MM-DD"},
        "due_date": {"type": ["string", "null"], "description": "ISO YYYY-MM-DD"},
        "currency": {"type": ["string", "null"], "description": "ISO code if known, otherwise the symbol from the document"},
        "issued_to": {
            "type": "object",
            "properties": {
                "name": {"type": ["string", "null"]},
                "company": {"type": ["string", "null"]},
                "address": {"type": ["string", "null"]},
            },
            "required": ["name", "company", "address"],
            "additionalProperties": False,
        },
        "pay_to": {
            "type": "object",
            "properties": {
                "bank": {"type": ["string", "null"]},
                "account_name": {"type": ["string", "null"]},
                "account_number": {"type": ["string", "null"]},
            },
            "required": ["bank", "account_name", "account_number"],
            "additionalProperties": False,
        },
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": ["string", "null"]},
                    "quantity": {"type": ["number", "null"]},
                    "unit_price": {"type": ["number", "null"]},
                    "total": {"type": ["number", "null"]},
                },
                "required": ["description", "quantity", "unit_price", "total"],
                "additionalProperties": False,
            },
        },
        "subtotal": {"type": ["number", "null"]},
        "tax_rate": {"type": ["number", "null"], "description": "Percent value, e.g. 10 for 10%"},
        "tax_amount": {"type": ["number", "null"]},
        "total": {"type": ["number", "null"]},
        "missing_fields": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Names of fields that could not be found in the document.",
        },
    },
    "required": [
        "document_type",
        "invoice_number",
        "policy_number",
        "incident_date",
        "issue_date",
        "due_date",
        "currency",
        "issued_to",
        "pay_to",
        "line_items",
        "subtotal",
        "tax_rate",
        "tax_amount",
        "total",
        "missing_fields",
    ],
    "additionalProperties": False,
}


SYSTEM_PROMPT = (
    "You are a precise document data extractor used by an insurance company's "
    "claims and underwriting team. You receive the raw text of a PDF document "
    "(invoice, insurance claim form, or supporting financial document) and "
    "return a strictly structured JSON object describing it.\n\n"
    "Rules:\n"
    "- First classify the document into document_type: claim_form for "
    "  insurance claim notifications (policy number present, incident details), "
    "  invoice for standard billing documents, otherwise other.\n"
    "- policy_number and incident_date are only populated for claim_form documents.\n"
    "- For claim forms, line_items represent itemized damage / repair costs.\n"
    "- Use null for any field that is not present. Do not guess.\n"
    "- Normalize dates to ISO 8601 (YYYY-MM-DD). DD.MM.YYYY and MM/DD/YYYY -> ISO.\n"
    "- Numeric fields must be numbers. Strip currency symbols and thousand separators.\n"
    "- currency: ISO 4217 code when symbol is unambiguous ($ -> USD, EUR -> EUR). "
    "  Slovak invoices typically use EUR.\n"
    "- tax_rate is the percent value (e.g. 20 for 20%), not a fraction.\n"
    "- missing_fields: list every top-level field set to null."
)


class LLMUnavailable(Exception):
    pass


def _coerce_invoice(payload: dict) -> Invoice:
    issued_to = payload.get("issued_to") or {}
    pay_to = payload.get("pay_to") or {}
    line_items = payload.get("line_items") or []

    return Invoice(
        document_type=payload.get("document_type") or "invoice",
        invoice_number=payload.get("invoice_number"),
        policy_number=payload.get("policy_number"),
        incident_date=payload.get("incident_date"),
        issue_date=payload.get("issue_date"),
        due_date=payload.get("due_date"),
        currency=payload.get("currency"),
        issued_to=Party(
            name=issued_to.get("name"),
            company=issued_to.get("company"),
            address=issued_to.get("address"),
        ),
        pay_to=PaymentDetails(
            bank=pay_to.get("bank"),
            account_name=pay_to.get("account_name"),
            account_number=pay_to.get("account_number"),
        ),
        line_items=[
            LineItem(
                description=li.get("description"),
                quantity=li.get("quantity"),
                unit_price=li.get("unit_price"),
                total=li.get("total"),
            )
            for li in line_items
        ],
        subtotal=payload.get("subtotal"),
        tax_rate=payload.get("tax_rate"),
        tax_amount=payload.get("tax_amount"),
        total=payload.get("total"),
        missing_fields=payload.get("missing_fields") or [],
    )


def extract_with_claude(raw_text: str) -> tuple[Invoice, str]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMUnavailable("ANTHROPIC_API_KEY not set")

    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise LLMUnavailable(f"anthropic SDK not installed: {exc}") from exc

    model = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7")
    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        output_config={
            "format": {
                "type": "json_schema",
                "name": "document",
                "schema": INVOICE_JSON_SCHEMA,
            }
        },
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract structured data from the following document text. "
                    "Return only the JSON object that matches the schema.\n\n"
                    f"<document>\n{raw_text}\n</document>"
                ),
            }
        ],
    )

    text = ""
    for block in response.content:
        if block.type == "text":
            text += block.text
    text = text.strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMUnavailable(f"Model returned non-JSON: {text[:200]}") from exc

    return _coerce_invoice(payload), model


def extract_heuristic(raw_text: str) -> Invoice:
    invoice = Invoice()

    def find(pattern: str, text: str = raw_text, flags: int = re.IGNORECASE) -> Optional[str]:
        m = re.search(pattern, text, flags)
        return m.group(1).strip() if m else None

    def to_iso(date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None
        m = re.match(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", date_str)
        if m:
            d, mo, y = m.groups()
            return f"{y}-{int(mo):02d}-{int(d):02d}"
        m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", date_str)
        if m:
            y, mo, d = m.groups()
            return f"{y}-{int(mo):02d}-{int(d):02d}"
        return date_str

    # Document type detection
    text_lower = raw_text.lower()
    is_claim = any(
        kw in text_lower
        for kw in ("poistnej udalosti", "skodov", "claim form", "policy", "poistnik", "havarijne")
    )
    invoice.document_type = "claim_form" if is_claim else "invoice"

    # Claim form specific fields
    if is_claim:
        invoice.invoice_number = find(r"(?:Cislo skodovej udalosti|Claim no\.?)[:\s]+([A-Z0-9-]+)")
        invoice.policy_number = find(r"(?:Cislo poistnej zmluvy|Policy no\.?)[:\s]+([A-Z0-9 -]+?)(?:\s{2,}|\n|$)")
        invoice.incident_date = to_iso(find(r"(?:Datum udalosti|Incident date)[:\s]+(\d{1,2}[./-]\d{1,2}[./-]\d{4})"))
        invoice.issue_date = to_iso(find(r"(?:Datum prijatia|Issue date|Date)[:\s]+(\d{1,2}[./-]\d{1,2}[./-]\d{4})"))
    else:
        invoice.invoice_number = find(r"INVOICE\s*NO[:\s]+([A-Z0-9-]+)")
        invoice.issue_date = to_iso(find(r"\bDATE[:\s]+(\d{1,2}[./-]\d{1,2}[./-]\d{4})"))
        invoice.due_date = to_iso(find(r"DUE\s*DATE[:\s]+(\d{1,2}[./-]\d{1,2}[./-]\d{4})"))

    # Issued to / counterparty (handles both column-flow invoice and label-based claim form)
    issued_match = re.search(
        r"ISSUED TO:[^\n]*\n([^\n]+)\n([^\n]+)\n([^\n]+)",
        raw_text,
        re.IGNORECASE,
    )
    if issued_match:
        def _strip_meta(s: str) -> str:
            return re.sub(r"\s+(DATE|DUE DATE|INVOICE NO):\s*.*$", "", s, flags=re.IGNORECASE).strip()
        invoice.issued_to.name = _strip_meta(issued_match.group(1))
        invoice.issued_to.company = _strip_meta(issued_match.group(2))
        invoice.issued_to.address = _strip_meta(issued_match.group(3))
    else:
        # Claim form style: "Meno a priezvisko: Jan Novak", "Adresa: ..."
        invoice.issued_to.name = find(r"(?:Meno a priezvisko|Name)[:\s]+([^\n]+?)(?:\s{2,}|\n|$)")
        invoice.issued_to.address = find(r"(?:Adresa|Address)[:\s]+([^\n]+?)(?:\s{2,}|\n|$)")

    # Payment block
    bank_match = re.search(r"(?:^|\n)([A-Z][A-Za-z]+ Bank|Tatra banka|VUB|SLSP|CSOB)\b", raw_text)
    if bank_match:
        invoice.pay_to.bank = bank_match.group(1).strip()
    invoice.pay_to.account_name = find(r"Account Name[:\s]+([^\n]+)")
    invoice.pay_to.account_number = find(r"Account No\.?[:\s]+([A-Z0-9 ]+?)(?:\s{2,}|\n|$)")

    # Totals
    invoice.subtotal = _to_float(find(r"(?:SUBTOTAL|Subtotal)[\s\$€]+([\d,]+\.?\d*)"))
    invoice.tax_rate = _to_float(find(r"(?:Tax|VAT|DPH)\s+([\d,]+\.?\d*)\s*%"))
    total_match = re.search(
        r"(?<!SUB)\bTOTAL\b[\s\$€]*([\d,]+\.\d{2}|[\d,]{2,})",
        raw_text,
        re.IGNORECASE,
    )
    if total_match:
        invoice.total = _to_float(total_match.group(1))
    if invoice.tax_rate is not None and invoice.subtotal is not None:
        invoice.tax_amount = round(invoice.subtotal * invoice.tax_rate / 100.0, 2)

    # Currency
    if "$" in raw_text:
        invoice.currency = "USD"
    elif "€" in raw_text or "EUR" in raw_text:
        invoice.currency = "EUR"

    # Line items — handles both invoice and claim-form layouts
    line_pattern = re.compile(
        r"^(?:\s+)?([A-Za-z][A-Za-z0-9 \-\.\(\)]+?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+\$\s*([\d,]+\.?\d*)\s*$",
        re.MULTILINE,
    )
    items: list[LineItem] = []
    for m in line_pattern.finditer(raw_text):
        desc, unit_price, qty, total = m.groups()
        desc = desc.strip()
        if desc.upper() in {"SUBTOTAL", "TOTAL", "TAX", "VAT"}:
            continue
        items.append(
            LineItem(
                description=desc,
                quantity=_to_float(qty),
                unit_price=_to_float(unit_price),
                total=_to_float(total),
            )
        )
    invoice.line_items = items

    # Missing fields
    missing: list[str] = []
    for field_name, value in invoice.model_dump().items():
        if field_name in ("missing_fields", "document_type"):
            continue
        # Skip claim-only fields on invoices and vice versa
        if not is_claim and field_name in ("policy_number", "incident_date"):
            continue
        if is_claim and field_name == "due_date":
            continue
        if value in (None, [], "", {}):
            missing.append(field_name)
        elif isinstance(value, dict) and all(v in (None, "") for v in value.values()):
            missing.append(field_name)
    invoice.missing_fields = missing
    return invoice


def _to_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    cleaned = value.replace(",", "").replace("$", "").replace("€", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None

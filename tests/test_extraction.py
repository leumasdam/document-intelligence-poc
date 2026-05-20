"""Unit tests for the heuristic extraction path (no API key required)."""
from pathlib import Path

from app.extractor import extract_invoice
from app.llm import _to_float, extract_heuristic

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample-data"


def test_to_float_strips_currency_and_separators():
    assert _to_float("$1,260.00") == 1260.0
    assert _to_float("€ 700") == 700.0
    assert _to_float("100") == 100.0


def test_to_float_returns_none_for_garbage():
    assert _to_float(None) is None
    assert _to_float("not a number") is None


def test_extract_heuristic_detects_claim_form():
    text = (
        "Oznamenie poistnej udalosti\n"
        "Cislo poistnej zmluvy: HV-99 88 77 66 55\n"
        "Datum udalosti: 14.05.2026\n"
        "Havarijne poistenie\n"
    )
    invoice = extract_heuristic(text)
    assert invoice.document_type == "claim_form"
    assert invoice.policy_number == "HV-99 88 77 66 55"
    assert invoice.incident_date == "2026-05-14"


def test_extract_heuristic_detects_plain_invoice():
    text = "INVOICE NO: 01234\nDATE: 11.02.2030\nSUBTOTAL $700\nTOTAL $770\n"
    invoice = extract_heuristic(text)
    assert invoice.document_type == "invoice"
    assert invoice.invoice_number == "01234"
    assert invoice.total == 770.0


def test_extract_invoice_on_sample_claim_pdf():
    pdf = (SAMPLE_DIR / "claim-form.pdf").read_bytes()
    result = extract_invoice(pdf)
    assert result.mode in {"llm", "heuristic"}
    assert result.invoice.document_type == "claim_form"
    assert result.invoice.total == 1260.0
    assert len(result.invoice.line_items) == 4
    assert len(result.word_boxes) > 0
    assert result.pdf_base64 is not None


def test_extract_invoice_on_sample_invoice_pdf():
    pdf = (SAMPLE_DIR / "invoice.pdf").read_bytes()
    result = extract_invoice(pdf)
    assert result.invoice.invoice_number == "01234"
    assert result.invoice.total == 770.0

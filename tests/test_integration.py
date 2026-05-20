"""Unit tests for the downstream integration routing logic."""
import re

from app.integration import _generate_case_id, _route_email


def test_case_id_format():
    cid = _generate_case_id("CR")
    assert re.match(r"^CR-\d{4}-\d{2}-\d{4}$", cid)


def test_classification_routes_by_category():
    assert _route_email({"category": "vehicle_damage"}, "classification") == "motor-claims@uniqa.sk"
    assert _route_email({"category": "complaint"}, "classification") == "complaints@uniqa.sk"


def test_summary_angry_routes_to_complaints():
    assert _route_email({"sentiment": "angry"}, "summary") == "complaints@uniqa.sk"
    assert _route_email({"sentiment": "neutral"}, "summary") == "claims-team@uniqa.sk"


def test_extraction_claim_routes_to_intake():
    assert _route_email({"document_type": "claim_form"}, "extraction") == "claims-intake@uniqa.sk"
    assert _route_email({"document_type": "invoice"}, "extraction") == "accounts-payable@uniqa.sk"


def test_unknown_category_falls_back_to_triage():
    assert _route_email({"category": "nonsense"}, "classification") == "triage@uniqa.sk"

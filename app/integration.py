"""Mock + optional real integration with downstream systems.

In a real UNIQA deployment, the structured output from Extract/Classify would
be pushed to the claims system (TIA / Guidewire / etc.), forwarded to the
relevant team mailbox, and logged for audit. This module simulates all three
and — if INTEGRATION_WEBHOOK_URL is configured — actually POSTs the payload to
a real HTTPS endpoint so you can demonstrate the end-to-end flow with a tool
like webhook.site.
"""
import asyncio
import json
import os
import random
import string
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Literal

WEBHOOK_URL = os.getenv("INTEGRATION_WEBHOOK_URL", "").strip() or None
MOCK_USER = os.getenv("MOCK_USER", "demo.user@uniqa.sk")


EMAIL_ROUTING = {
    "vehicle_damage": "motor-claims@uniqa.sk",
    "property_damage": "property-claims@uniqa.sk",
    "health_claim": "health-claims@uniqa.sk",
    "travel_claim": "travel-claims@uniqa.sk",
    "complaint": "complaints@uniqa.sk",
    "payment_issue": "billing@uniqa.sk",
    "policy_change": "policy-admin@uniqa.sk",
    "document_update": "customer-service@uniqa.sk",
    "policy_question": "customer-service@uniqa.sk",
    "cancellation": "cancellations@uniqa.sk",
    "other": "triage@uniqa.sk",
}


def _generate_case_id(prefix: str) -> str:
    ym = datetime.now(timezone.utc).strftime("%Y-%m")
    suffix = "".join(random.choices(string.digits, k=4))
    return f"{prefix}-{ym}-{suffix}"


def _route_email(payload: dict, kind: str) -> str:
    if kind == "classification":
        return EMAIL_ROUTING.get(payload.get("category", "other"), "triage@uniqa.sk")
    if kind == "summary":
        # Dissatisfied customers go to the complaints desk; the rest to claims.
        if payload.get("sentiment") in ("angry", "frustrated"):
            return "complaints@uniqa.sk"
        return "claims-team@uniqa.sk"
    # extraction
    doc_type = payload.get("document_type", "invoice")
    if doc_type == "claim_form":
        return "claims-intake@uniqa.sk"
    return "accounts-payable@uniqa.sk"


def _truncate_url(url: str, keep: int = 40) -> str:
    if len(url) <= keep:
        return url
    return url[:keep] + "..."


def _post_webhook_sync(url: str, body: dict) -> tuple[Literal["delivered", "failed"], str | None, int | None]:
    """Blocking POST — run in a worker thread to keep async loop free."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "uniqa-document-intelligence-poc/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            return ("delivered" if status < 400 else "failed", None, status)
    except urllib.error.HTTPError as exc:
        return ("failed", f"HTTP {exc.code}: {exc.reason}", exc.code)
    except Exception as exc:
        return ("failed", str(exc), None)


async def deliver(payload: dict, kind: Literal["extraction", "classification"]) -> dict[str, Any]:
    """Simulate routing + (optionally) post to real webhook.

    Always returns the metadata you would see in a real system. If a webhook
    URL is configured, also performs the POST and reports the outcome.
    """
    case_prefix = "TIA" if kind == "extraction" else "CR"
    case_id = _generate_case_id(case_prefix)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    recipient = _route_email(payload, kind)

    body = {
        "case_id": case_id,
        "kind": kind,
        "timestamp": timestamp,
        "recipient": recipient,
        "audited_by": MOCK_USER,
        "data": payload,
    }

    webhook_status = "not_configured"
    webhook_url_display = None
    webhook_error = None
    webhook_http_status = None

    if WEBHOOK_URL:
        webhook_url_display = _truncate_url(WEBHOOK_URL)
        status, error, http_status = await asyncio.to_thread(_post_webhook_sync, WEBHOOK_URL, body)
        webhook_status = status
        webhook_error = error
        webhook_http_status = http_status

    return {
        "case_id": case_id,
        "recipient_email": recipient,
        "audited_by": MOCK_USER,
        "timestamp": timestamp,
        "webhook_status": webhook_status,
        "webhook_url": webhook_url_display,
        "webhook_http_status": webhook_http_status,
        "webhook_error": webhook_error,
    }

"""Case classification & routing for incoming customer messages.

Same dual-mode design as the PDF extractor: Claude when ANTHROPIC_API_KEY is
present, deterministic keyword heuristic otherwise.
"""
import json
import os

from .schemas import Classification


CATEGORY_LABELS = {
    "vehicle_damage": "Vehicle damage",
    "property_damage": "Property damage",
    "health_claim": "Health claim",
    "travel_claim": "Travel claim",
    "policy_change": "Policy change",
    "payment_issue": "Payment / billing issue",
    "document_update": "Document update",
    "complaint": "Complaint",
    "cancellation": "Cancellation request",
    "policy_question": "Policy question",
    "other": "Other / unclassified",
}

CATEGORY_TEAM = {
    "vehicle_damage": "Motor Claims Team",
    "property_damage": "Property Claims Team",
    "health_claim": "Health Claims Team",
    "travel_claim": "Travel Claims Team",
    "policy_change": "Policy Administration",
    "payment_issue": "Billing & Reimbursement",
    "document_update": "Customer Service",
    "complaint": "Complaints Officer",
    "cancellation": "Cancellations Desk",
    "policy_question": "Customer Service",
    "other": "Triage Desk",
}

DEFAULT_ACTIONS = {
    "vehicle_damage": [
        "Verify policy is active and covers the reported damage",
        "Request police report and photo evidence if not attached",
        "Schedule vehicle inspection at a partner workshop",
    ],
    "property_damage": [
        "Verify the property address matches the policy",
        "Request photos and a damage assessment",
        "Schedule on-site inspection if reported damage > 5,000 EUR",
    ],
    "complaint": [
        "Acknowledge receipt within 24 hours per SLA",
        "Forward to the Complaints Officer for formal handling",
        "Flag for legal review if regulatory bodies are mentioned",
    ],
    "payment_issue": [
        "Pull payment history for the cited claim or invoice",
        "Verify the bank account on file matches the request",
        "Escalate to billing team for urgent resolution",
    ],
    "policy_change": [
        "Verify customer identity per KYC requirements",
        "Update the policy in system and generate an amendment",
        "Send written confirmation to the customer",
    ],
    "document_update": [
        "Verify customer identity",
        "Update contact details across all active policies",
        "Send confirmation",
    ],
    "policy_question": [
        "Identify the relevant policy clauses",
        "Provide a written response within 48 hours",
    ],
    "cancellation": [
        "Verify customer identity",
        "Check cancellation terms and refund eligibility",
        "Process termination per policy terms",
    ],
    "health_claim": [
        "Request medical documentation",
        "Verify treatment was in-network if applicable",
        "Process per health insurance terms",
    ],
    "travel_claim": [
        "Request travel documentation and receipts",
        "Verify travel insurance was active during the incident",
    ],
    "other": [
        "Manual triage required",
        "Review content and route to the appropriate team",
    ],
}


CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": list(CATEGORY_LABELS.keys()),
            "description": "Single best-fit category from the enum.",
        },
        "category_label": {"type": "string", "description": "Human-readable category name."},
        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
        "route_to": {"type": "string", "description": "Internal team name that should own this case."},
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Model self-assessment of classification certainty.",
        },
        "reason": {
            "type": "string",
            "description": "One-to-two-sentence explanation tying classification to specific phrases in the message. "
            "Use the same language as the input message.",
        },
        "suggested_actions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Two to four concrete next actions for the adjuster.",
        },
        "detected_language": {
            "type": ["string", "null"],
            "description": "ISO 639-1 code (e.g. 'sk', 'en', 'de').",
        },
    },
    "required": [
        "category",
        "category_label",
        "priority",
        "route_to",
        "confidence",
        "reason",
        "suggested_actions",
        "detected_language",
    ],
    "additionalProperties": False,
}


SYSTEM_PROMPT = (
    "You are a triage assistant for an insurance company. You receive an "
    "incoming customer message (email, claim description, complaint, "
    "question) and classify it so it can be routed to the right team.\n\n"
    "Rules:\n"
    "- Pick a single best-fit category from the enum.\n"
    "- priority='high' for: legal threats (NBS, ŠOI, court, lawyer, sue), "
    "active emergencies (hospital, injury), explicit deadlines under 48h, "
    "large monetary amounts in dispute (>5000 EUR).\n"
    "- priority='low' for: pure policy questions without an active claim, "
    "address/contact updates, general info requests.\n"
    "- Otherwise priority='medium'.\n"
    "- route_to: pick from {Motor Claims Team, Property Claims Team, "
    "Health Claims Team, Travel Claims Team, Policy Administration, "
    "Billing & Reimbursement, Customer Service, Complaints Officer, "
    "Cancellations Desk, Triage Desk}.\n"
    "- reason: 1-2 sentences in the same language as the input, citing "
    "specific phrases that drove the classification.\n"
    "- suggested_actions: 2-4 concrete operational steps for the adjuster."
)


# ---------------------------------------------------------------------------
# Heuristic fallback


def _normalize(text: str) -> str:
    mapping = str.maketrans(
        "áäčďéíĺľňóôŕšťúýžÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽ",
        "aacdeillnoorstuyzAACDEILLNOORSTUYZ",
    )
    return text.translate(mapping).lower()


KEYWORD_MAP = [
    ("vehicle_damage", [
        "nehoda", "dopravna nehoda", "naraznik", "blatnik", "svetlo",
        "vozidlo", "kasko", "pzp", "auto",
        "accident", "vehicle", "car crash", "collision", "bumper",
    ]),
    ("property_damage", [
        "strecha", "byt", "dom", "voda", "vykurovanie", "burka",
        "vichor", "krupy", "poziar",
        "house", "flood", "fire", "storm", "roof",
    ]),
    ("health_claim", [
        "zdravotn", "operacia", "nemocn", "lekar", "hospitalizacia",
        "uraz", "zranenie",
        "hospital", "medical", "surgery", "injury",
    ]),
    ("travel_claim", [
        "dovolenka", "cestovne", "zahranicie", "letenka", "batozina",
        "travel", "abroad", "luggage",
    ]),
    ("payment_issue", [
        "platba", "neuhraden", "nedoplatok", "premia", "splatnost",
        "vyplat", "preplat",
        "payment", "invoice", "premium", "overdue", "reimburs", "billing",
    ]),
    ("complaint", [
        "staznost", "nespokojn", "reklamacia",
        "complaint", "unhappy", "dissatisfied",
    ]),
    ("cancellation", [
        "zrusenie", "vypoved", "ukoncenie",
        "cancel", "terminate", "end policy",
    ]),
    ("document_update", [
        "zmena adresy", "novy email", "novy telefon", "kontakt",
        "address change", "email update",
    ]),
    ("policy_change", [
        "zmena zmluvy", "uprava", "rozsirenie", "pripoistenie",
        "amendment", "change policy", "extend",
    ]),
    ("policy_question", [
        "otazka", "informaciu", "uvazujem", "zaujimalo", "ma zaujima",
        "question", "wondering", "info request",
    ]),
]

HIGH_PRIORITY_KEYWORDS = [
    "nbs", "soi", "narodna banka", "obchodna inspekcia",
    "sudu", "sudne", "pravnik", "advokat", "zaloba",
    "court", "lawyer", "attorney", "sue", "legal action",
    "nemocnica", "hospitalizovan", "zranen", "smrt",
    "hospital", "injury", "death", "emergency",
    "okamzit", "urgentne", "surne", "kriticky",
    "urgent", "immediate", "critical", "asap",
]

LOW_PRIORITY_CATEGORIES = {"policy_question", "document_update"}


def classify_heuristic(text: str) -> Classification:
    norm = _normalize(text)

    category = "other"
    confidence = 0.4
    matched_kw = None

    # Strong, low-ambiguity phrases first — these beat generic single-word matches
    # like "auto" / "PZP" which appear in many contexts.
    strong_phrases = [
        ("document_update", ["zmena adresy", "novu adresu", "novy email", "address change", "email update"]),
        ("complaint", ["staznost", "nespokojn", "narodna banka", "obchodna inspekcia", "soi", "nbs", "complaint"]),
        ("cancellation", ["zrusit zmluvu", "vypoved zmluvy", "ukoncit poistku", "cancel my policy", "terminate"]),
        ("policy_question", ["uvazujem o", "zaujimalo by ma", "ma zaujima", "informaciu", "wondering if", "could you tell"]),
    ]
    for cat, phrases in strong_phrases:
        for phrase in phrases:
            if phrase in norm:
                category = cat
                confidence = 0.7
                matched_kw = phrase
                break
        if category != "other":
            break

    # Fallback to single-keyword scan if nothing strong matched.
    if category == "other":
        for cat, kws in KEYWORD_MAP:
            for kw in kws:
                if kw in norm:
                    category = cat
                    confidence = 0.6
                    matched_kw = kw
                    break
            if category != "other":
                break

    priority = "medium"
    if any(kw in norm for kw in HIGH_PRIORITY_KEYWORDS):
        priority = "high"
        confidence = min(confidence + 0.1, 0.85)
    elif category in LOW_PRIORITY_CATEGORIES:
        priority = "low"

    sk_indicators = ["dobry den", "dakujem", "prosim", "podla", "som", "vam", "vasej"]
    detected_language = "sk" if any(ind in norm for ind in sk_indicators) else "en"

    reason = (
        f"Keyword '{matched_kw}' matched category '{CATEGORY_LABELS.get(category)}'. "
        f"Heuristic fallback — for nuanced classification, configure ANTHROPIC_API_KEY."
        if matched_kw
        else "No category keywords matched. Routed to Triage Desk for manual review."
    )

    return Classification(
        category=category,
        category_label=CATEGORY_LABELS.get(category, "Other"),
        priority=priority,
        route_to=CATEGORY_TEAM.get(category, "Triage Desk"),
        confidence=confidence,
        reason=reason,
        suggested_actions=DEFAULT_ACTIONS.get(category, ["Manual review required"]),
        detected_language=detected_language,
    )


# ---------------------------------------------------------------------------
# LLM path


class LLMUnavailable(Exception):
    pass


def classify_with_claude(text: str) -> tuple[Classification, str]:
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
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        output_config={
            "format": {
                "type": "json_schema",
                "name": "case_classification",
                "schema": CLASSIFICATION_SCHEMA,
            }
        },
        messages=[
            {
                "role": "user",
                "content": (
                    "Classify the following customer message. Return only the JSON object.\n\n"
                    f"<message>\n{text}\n</message>"
                ),
            }
        ],
    )

    body = ""
    for block in response.content:
        if block.type == "text":
            body += block.text
    body = body.strip()

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise LLMUnavailable(f"Model returned non-JSON: {body[:200]}") from exc

    return (
        Classification(
            category=payload.get("category", "other"),
            category_label=payload.get("category_label") or CATEGORY_LABELS.get(payload.get("category", "other"), "Other"),
            priority=payload.get("priority", "medium"),
            route_to=payload.get("route_to") or CATEGORY_TEAM.get(payload.get("category", "other"), "Triage Desk"),
            confidence=float(payload.get("confidence", 0.5)),
            reason=payload.get("reason", ""),
            suggested_actions=payload.get("suggested_actions") or [],
            detected_language=payload.get("detected_language"),
        ),
        model,
    )


def classify(text: str) -> tuple[Classification, str, str | None]:
    """Returns (classification, mode, model)."""
    try:
        cls, model = classify_with_claude(text)
        return cls, "llm", model
    except LLMUnavailable:
        return classify_heuristic(text), "heuristic", None

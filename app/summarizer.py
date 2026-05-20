"""Document summarization & response drafting.

Turns a long claim narrative / email thread into an executive summary, key
facts, a suggested next action, and a customer-facing response draft.

Same dual-mode pattern as the other tools: Claude when ANTHROPIC_API_KEY is
present, a deterministic extractive heuristic otherwise. The heuristic is
honestly weaker here — summarization is exactly the task where an LLM pulls
far ahead of regex — and the UI says so.
"""
import json
import os
import re

from .schemas import Summary


SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "executive_summary": {
            "type": "string",
            "description": "2-3 sentence summary a claims supervisor could read in 10 seconds.",
        },
        "key_facts": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3-6 bullet-point facts: dates, amounts, policy numbers, parties, what is missing.",
        },
        "suggested_action": {
            "type": "string",
            "description": "The single most important next step for the adjuster.",
        },
        "customer_response_draft": {
            "type": "string",
            "description": "A polite, professional draft reply to the customer, in the customer's language. "
            "Ready for the adjuster to review and send.",
        },
        "sentiment": {
            "type": "string",
            "enum": ["satisfied", "neutral", "frustrated", "angry"],
            "description": "The customer's emotional tone.",
        },
        "detected_language": {
            "type": ["string", "null"],
            "description": "ISO 639-1 code of the input text.",
        },
    },
    "required": [
        "executive_summary",
        "key_facts",
        "suggested_action",
        "customer_response_draft",
        "sentiment",
        "detected_language",
    ],
    "additionalProperties": False,
}


SYSTEM_PROMPT = (
    "You are an assistant for an insurance company's claims team. You receive "
    "a long customer message, claim narrative, or email thread and produce a "
    "concise, structured summary that lets a busy adjuster act fast.\n\n"
    "Rules:\n"
    "- executive_summary: 2-3 sentences, no fluff, what a supervisor needs.\n"
    "- key_facts: concrete data points — dates, amounts, policy/claim numbers, "
    "parties, and explicitly note anything important that is MISSING.\n"
    "- suggested_action: the single most important next step.\n"
    "- customer_response_draft: a polite, professional reply IN THE CUSTOMER'S "
    "LANGUAGE. Acknowledge their situation, state the next step, set an "
    "expectation. Do not promise specific payouts or admit liability.\n"
    "- sentiment: gauge the customer's tone honestly.\n"
    "- Write summary fields in the same language as the input."
)


class LLMUnavailable(Exception):
    pass


def summarize_with_claude(text: str) -> tuple[Summary, str]:
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
        max_tokens=3072,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        output_config={
            "format": {
                "type": "json_schema",
                "name": "claim_summary",
                "schema": SUMMARY_SCHEMA,
            }
        },
        messages=[
            {
                "role": "user",
                "content": (
                    "Summarize the following customer message / claim narrative. "
                    "Return only the JSON object.\n\n"
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
        Summary(
            executive_summary=payload.get("executive_summary", ""),
            key_facts=payload.get("key_facts") or [],
            suggested_action=payload.get("suggested_action", ""),
            customer_response_draft=payload.get("customer_response_draft", ""),
            sentiment=payload.get("sentiment", "neutral"),
            detected_language=payload.get("detected_language"),
        ),
        model,
    )


# ---------------------------------------------------------------------------
# Heuristic fallback — extractive, deliberately simple


def _split_sentences(text: str) -> list[str]:
    # Drop email-thread separator lines like "--- Reply, 6.5.2026 ---".
    cleaned = re.sub(r"-{2,}[^\n]*-{2,}", " ", text)
    parts = re.split(r"(?<=[.!?])\s+", cleaned.replace("\n", " "))
    return [p.strip() for p in parts if len(p.strip()) > 15]


def _normalize(text: str) -> str:
    mapping = str.maketrans(
        "áäčďéíĺľňóôŕšťúýžÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽ",
        "aacdeillnoorstuyzAACDEILLNOORSTUYZ",
    )
    return text.translate(mapping).lower()


FACT_MARKERS = [
    r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}",  # dates
    r"\d+[\s.,]?\d*\s?(?:eur|€|\$|usd)",  # amounts
    r"[A-Z]{2,}-?\s?\d",  # policy/claim numbers
    r"\biban\b|\bsk\d{2}\b",  # bank
]

ANGRY_WORDS = ["nahnevany", "skandal", "neakceptovatel", "zaloba", "sud", "ombudsman",
               "narodna banka", "pravne kroky", "zasadne nesuhlas", "takto sa",
               "outraged", "unacceptable", "lawyer", "sue", "disgrace", "legal action"]
FRUSTRATED_WORDS = ["uz druhy mesiac", "opakovane", "ziadna odpoved", "uz raz som",
                    "ledva", "bojim sa", "neprijemne", "still no", "no response",
                    "frustrated", "third time", "again and again"]
# Genuine satisfaction only — bare politeness ("ďakujem za odpoveď") does not count.
HAPPY_WORDS = ["som velmi spokojny", "vyborna sluzba", "velmi ocenujem", "dakujem za rychle",
               "perfektny pristup", "very satisfied", "excellent service", "great service"]


def summarize_heuristic(text: str) -> Summary:
    sentences = _split_sentences(text)
    norm = _normalize(text)

    # Executive summary: first 2 substantive sentences.
    summary = " ".join(sentences[:2]) if sentences else text[:240]
    if len(summary) > 320:
        summary = summary[:317] + "..."

    # Key facts: sentences containing dates / amounts / IDs.
    key_facts: list[str] = []
    fact_re = re.compile("|".join(FACT_MARKERS), re.IGNORECASE)
    for s in sentences:
        if fact_re.search(s) and len(key_facts) < 6:
            fact = s if len(s) <= 160 else s[:157] + "..."
            key_facts.append(fact)
    if not key_facts:
        key_facts = ["No structured facts (dates / amounts / IDs) detected by the heuristic."]

    # Sentiment
    if any(w in norm for w in ANGRY_WORDS):
        sentiment = "angry"
    elif any(w in norm for w in FRUSTRATED_WORDS):
        sentiment = "frustrated"
    elif any(w in norm for w in HAPPY_WORDS):
        sentiment = "satisfied"
    else:
        sentiment = "neutral"

    # Language
    sk_indicators = ["dobry den", "dakujem", "prosim", "podla", "som", "vam"]
    detected_language = "sk" if any(i in norm for i in sk_indicators) else "en"

    # Suggested action
    if sentiment in ("angry", "frustrated"):
        suggested_action = (
            "Priority response — customer is dissatisfied. Acknowledge within "
            "24h and assign an owner before the case escalates."
        )
    else:
        suggested_action = "Review the key facts, request any missing documentation, and respond to the customer."

    # Customer response draft — template
    if detected_language == "sk":
        customer_response_draft = (
            "Dobrý deň,\n\n"
            "ďakujeme za Vašu správu. Vašu požiadavku sme zaevidovali a "
            "postupujeme ju príslušnému tímu na spracovanie. O ďalšom postupe "
            "Vás budeme informovať najneskôr do 5 pracovných dní.\n\n"
            "S pozdravom,\nTím likvidácie poistných udalostí"
        )
    else:
        customer_response_draft = (
            "Dear customer,\n\n"
            "thank you for your message. We have registered your request and "
            "forwarded it to the responsible team. We will update you on the "
            "next steps within 5 business days.\n\n"
            "Kind regards,\nClaims Team"
        )

    return Summary(
        executive_summary=summary,
        key_facts=key_facts,
        suggested_action=suggested_action,
        customer_response_draft=customer_response_draft,
        sentiment=sentiment,
        detected_language=detected_language,
    )


def summarize(text: str) -> tuple[Summary, str, str | None]:
    """Returns (summary, mode, model)."""
    try:
        s, model = summarize_with_claude(text)
        return s, "llm", model
    except LLMUnavailable:
        return summarize_heuristic(text), "heuristic", None

import base64

from .llm import LLMUnavailable, extract_heuristic, extract_with_claude
from .pdf_reader import extract_text_and_boxes
from .schemas import ExtractionResponse


def extract_invoice(pdf_bytes: bytes) -> ExtractionResponse:
    raw_text, boxes, pages = extract_text_and_boxes(pdf_bytes)
    pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")

    try:
        invoice, model = extract_with_claude(raw_text)
        mode = "llm"
    except LLMUnavailable:
        invoice = extract_heuristic(raw_text)
        model = None
        mode = "heuristic"

    return ExtractionResponse(
        invoice=invoice,
        raw_text=raw_text,
        mode=mode,
        model=model,
        pdf_base64=pdf_b64,
        word_boxes=boxes,
        pages=pages,
    )

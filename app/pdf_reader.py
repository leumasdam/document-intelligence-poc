import pdfplumber
from io import BytesIO

from .schemas import PageSize, WordBox


def extract_text(pdf_bytes: bytes) -> str:
    text_parts: list[str] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts).strip()


def extract_text_and_boxes(pdf_bytes: bytes) -> tuple[str, list[WordBox], list[PageSize]]:
    text_parts: list[str] = []
    boxes: list[WordBox] = []
    pages: list[PageSize] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            text_parts.append(page.extract_text() or "")
            pages.append(PageSize(page=i, width=float(page.width), height=float(page.height)))
            for word in page.extract_words():
                boxes.append(
                    WordBox(
                        text=word["text"],
                        x0=float(word["x0"]),
                        y0=float(word["top"]),
                        x1=float(word["x1"]),
                        y1=float(word["bottom"]),
                        page=i,
                    )
                )
    return "\n".join(text_parts).strip(), boxes, pages

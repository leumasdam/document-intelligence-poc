from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .classifier import classify
from .extractor import extract_invoice
from .integration import deliver
from .samples import SAMPLE_CASES, SAMPLE_NARRATIVES
from .schemas import (
    ClassificationRequest,
    ClassificationResponse,
    ExtractionResponse,
    IntegrationRequest,
    IntegrationResult,
    SummaryRequest,
    SummaryResponse,
)
from .summarizer import summarize

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
SAMPLES = {
    "invoice": ROOT / "sample-data" / "invoice.pdf",
    "claim": ROOT / "sample-data" / "claim-form.pdf",
}

app = FastAPI(title="PDF Data Extraction Assistant", version="0.3.0")


@app.middleware("http")
async def revalidate_static(request, call_next):
    """Force browsers to revalidate the HTML/JS/CSS on every load.

    `no-cache` keeps the asset cached but requires a conditional request
    before reuse — the server answers 304 when unchanged. This prevents the
    stale-JavaScript problem where a returning visitor runs an old app.js
    against a freshly deployed index.html.
    """
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/sample")
@app.get("/sample/{kind}")
async def sample(kind: str = "claim"):
    path = SAMPLES.get(kind)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail=f"Sample '{kind}' not found.")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@app.get("/sample-case")
async def list_sample_cases():
    return {kind: {"title": data["title"]} for kind, data in SAMPLE_CASES.items()}


@app.get("/sample-case/{kind}")
async def get_sample_case(kind: str):
    if kind not in SAMPLE_CASES:
        raise HTTPException(status_code=404, detail=f"Sample case '{kind}' not found.")
    return SAMPLE_CASES[kind]


@app.post("/classify", response_model=ClassificationResponse)
async def classify_case(payload: ClassificationRequest):
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message text is required.")
    if len(text) > 20000:
        raise HTTPException(status_code=413, detail="Message too long (max 20,000 chars).")
    classification, mode, model = classify(text)
    return ClassificationResponse(classification=classification, mode=mode, model=model)


@app.get("/sample-narrative")
async def list_sample_narratives():
    return {kind: {"title": data["title"]} for kind, data in SAMPLE_NARRATIVES.items()}


@app.get("/sample-narrative/{kind}")
async def get_sample_narrative(kind: str):
    if kind not in SAMPLE_NARRATIVES:
        raise HTTPException(status_code=404, detail=f"Sample narrative '{kind}' not found.")
    return SAMPLE_NARRATIVES[kind]


@app.post("/summarize", response_model=SummaryResponse)
async def summarize_document(payload: SummaryRequest):
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message text is required.")
    if len(text) > 30000:
        raise HTTPException(status_code=413, detail="Message too long (max 30,000 chars).")
    summary, mode, model = summarize(text)
    return SummaryResponse(summary=summary, mode=mode, model=model)


@app.post("/integrate", response_model=IntegrationResult)
async def integrate(req: IntegrationRequest):
    if not req.payload:
        raise HTTPException(status_code=400, detail="Payload is required.")
    result = await deliver(req.payload, req.kind)
    return IntegrationResult(**result)


@app.post("/extract", response_model=ExtractionResponse)
async def extract(file: UploadFile = File(...)):
    if file.content_type not in {"application/pdf", "application/octet-stream"} and not (
        file.filename or ""
    ).lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        return extract_invoice(pdf_bytes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {exc}") from exc


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")

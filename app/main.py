from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .extractor import extract_invoice
from .schemas import ExtractionResponse

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
SAMPLES = {
    "invoice": ROOT / "sample-data" / "invoice.pdf",
    "claim": ROOT / "sample-data" / "claim-form.pdf",
}

app = FastAPI(title="PDF Data Extraction Assistant", version="0.2.0")


@app.get("/sample")
@app.get("/sample/{kind}")
async def sample(kind: str = "claim"):
    path = SAMPLES.get(kind)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail=f"Sample '{kind}' not found.")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


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

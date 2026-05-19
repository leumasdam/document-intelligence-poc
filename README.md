# UNIQA · Document Intelligence (concept)

A portfolio case-study for AI-assisted document processing in an insurance back office.
Drop a PDF claim form or invoice — the AI extracts a structured JSON, highlights low-confidence
fields for review, and lets the adjuster click any field to verify its source on the original PDF.

> Concept demo, not affiliated with or endorsed by UNIQA Insurance Group. Branding is used
> illustratively for portfolio purposes.

## What it does

- **Input:** PDF claim form, invoice, or supporting document
- **Output:** structured JSON (claim/document number, policy number, dates, parties,
  line items, totals) plus a `missing_fields` list flagging anything the model could not
  confidently extract
- **UI:** drag-drop upload, **side-by-side PDF preview**, **click-to-highlight** —
  every field shows where it came from on the source PDF
- **Time-saved counter** in the header accumulates across uploads so reviewers see the
  cumulative impact of the tool
- **Two sample documents** ship in the box: a Slovak car-insurance claim form
  (`sample-data/claim-form.pdf`) and a generic invoice (`sample-data/invoice.pdf`)

The form deliberately treats AI output as a *proposal*, not a decision: missing or
low-confidence fields are highlighted in amber for the adjuster's review.

## Architecture

```
PDF upload
  -> pdfplumber (text + per-word bounding boxes)
    -> Claude (Opus 4.7 with adaptive thinking + output_config.format JSON schema)
      -> Pydantic validation
        -> reviewable form + PDF preview with click-to-highlight + downloadable JSON
```

If no `ANTHROPIC_API_KEY` is set, the app falls back to a regex-based heuristic
extractor so the demo works end-to-end without external dependencies. The UI shows
which mode was used.

## Run locally

```powershell
# 1. Install deps (once)
python -m pip install -r requirements.txt

# 2. (Optional) Add your API key for the LLM path
copy .env.example .env
# Then edit .env and set ANTHROPIC_API_KEY=sk-ant-...

# 3. Start the server
.\run.ps1
# or the raw command:
python -m uvicorn app.main:app --reload --app-dir .
```

Open <http://127.0.0.1:8000> and either drop a PDF or click one of the sample buttons.

## Deploy

The repo includes a `Dockerfile` and a `render.yaml` blueprint. Easiest path:

1. Push this folder to a GitHub repo.
2. On <https://render.com>, **New > Blueprint** and point at the repo.
3. Render auto-detects `render.yaml`. Add `ANTHROPIC_API_KEY` as a secret env var
   when prompted (or leave empty to deploy in heuristic mode).
4. First deploy takes ~3 minutes. Free tier sleeps after 15 min idle and cold-starts
   in ~30s — fine for a portfolio demo.

The same Docker image runs on **Fly.io**, **Railway**, **Google Cloud Run**, or any
container host.

## Project layout

```
app/
  main.py        FastAPI app, routes, static serving
  extractor.py   Orchestration: PDF -> LLM (or heuristic)
  pdf_reader.py  pdfplumber wrapper, returns text + per-word bounding boxes
  llm.py         Claude client, JSON schema, heuristic fallback, doc-type detection
  schemas.py     Pydantic models (Invoice, LineItem, WordBox, ...)
static/
  index.html     UI shell, Tailwind via CDN, lucide icons, PDF.js loader
  app.js         Upload, render, PDF preview, click-to-highlight, time counter
  style.css      Custom styling
sample-data/
  invoice.pdf      Generic invoice
  claim-form.pdf   Slovak car-insurance claim form (generated, see scripts/)
scripts/
  generate_claim_sample.py  fpdf2 generator for the claim form sample
Dockerfile     Container build
render.yaml    Render blueprint
run.ps1        Local launcher
```

## Standout features (for portfolio show-and-tell)

1. **Click any field, see it on the PDF** — pdfplumber's word boxes are surfaced
   to the frontend and matched against the value you click. This is the
   "decision-support" loop in one interaction.
2. **Document type auto-detection** — the same backend handles invoices and claim
   forms; the UI hides fields irrelevant to the detected type.
3. **Time-saved counter** — quantifies the value proposition in the UI itself.
   Persists across uploads via localStorage.
4. **Graceful degradation** — no API key? Falls back to a regex extractor so the
   demo still works for anyone who clones the repo.

## Next steps to production

- Authentication, audit log, per-claim history
- Persist extractions + reviewer corrections (corrections are training data)
- LLM-returned confidence scores per field (not just a binary missing flag)
- Multi-page support already works; multi-document batch upload would be 1 day's work
- Replace heuristic fallback with a model-distilled small classifier so
  offline-mode quality matches online-mode
- Wire export to a real claims system (TIA, Guidewire, etc.) via webhook

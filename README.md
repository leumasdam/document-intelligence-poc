# UNIQA · Document Intelligence (concept)

A portfolio case-study for AI-assisted back-office automation in insurance. Two
tools under one workspace, switched via the header nav:

1. **Extract** — drop a PDF claim form or invoice, get structured JSON with
   click-to-highlight verification on the source PDF
2. **Classify** — paste an incoming email / message, get category, priority,
   routing team, confidence score and suggested adjuster actions

> Concept demo, not affiliated with or endorsed by UNIQA Insurance Group. Branding is used
> illustratively for portfolio purposes.

## What it does

### Extract mode (PDF → structured JSON)
- **Input:** PDF claim form, invoice, or supporting document
- **Output:** structured JSON (claim/document number, policy number, dates,
  parties, line items, totals) plus a `missing_fields` list flagging anything
  the model could not confidently extract
- **UI:** drag-drop upload, side-by-side PDF preview, **click-to-highlight** —
  every field shows where it came from on the source PDF
- **Two sample documents** ship in the box: a Slovak car-insurance claim form
  and a generic invoice

### Classify mode (text → category + team + priority)
- **Input:** plain text (email body, claim description, complaint, question)
- **Output:** category (vehicle damage / property / health / payment /
  complaint / policy change / …), priority (high / medium / low), routing
  team, confidence score, reasoning, suggested adjuster actions
- **Four sample cases** built in: car accident, payment complaint, address
  change, policy question
- **High-priority signals** include legal threats (NBS / ŠOI / lawyer mentions)
  and active emergencies — surfaces red badge for immediate triage

### Shared
- **Time-saved counter** in the header accumulates across both tools
  (~8 min per extraction, ~3 min per classification) — persists across sessions
  via localStorage
- Forms deliberately treat AI output as a *proposal*, not a decision: missing
  or low-confidence fields are highlighted in amber for the adjuster's review
- **Mock or real downstream integration** — clicking "Approve & route" /
  "Save & export" generates a fake case ID and routes to a team mailbox by
  default. If `INTEGRATION_WEBHOOK_URL` is set, the same action also POSTs the
  payload to that URL (e.g. webhook.site for live demonstration)

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
4. (Optional) For the **real webhook integration**, also add
   `INTEGRATION_WEBHOOK_URL` — see the next section.
5. First deploy takes ~3 minutes. Free tier sleeps after 15 min idle and cold-starts
   in ~30s — fine for a portfolio demo.

The same Docker image runs on **Fly.io**, **Railway**, **Google Cloud Run**, or any
container host.

## Demonstrating the real webhook integration

For interviews, it's powerful to show that the tool actually pushes data
somewhere — not just generates JSON on screen. Set this up once:

1. Open <https://webhook.site> in a new tab. It gives you a unique URL (copied
   to your clipboard automatically). Free, no signup needed.
2. In Render dashboard → your service → **Environment**, add
   `INTEGRATION_WEBHOOK_URL` with that webhook.site URL as the value. Save.
3. Render redeploys automatically (~30s).
4. In the demo, open both the app and the webhook.site tab side by side.
   Click **Approve & route** (Classify) or **Save & export** (Extract) — the
   payload appears in webhook.site in real time, the result card in the app
   shows a green "live webhook" badge, and the HTTP status code.

When the env var is not set, both buttons still work — they just show a
"mock" badge instead of "live webhook" and skip the actual HTTP POST. This
keeps the demo functional without any setup, while the env var unlocks the
production-style integration view.

## Project layout

```
app/
  main.py        FastAPI app, routes, static serving
  extractor.py   Extract orchestration: PDF -> LLM (or heuristic)
  pdf_reader.py  pdfplumber wrapper, text + per-word bounding boxes
  llm.py         Claude client, JSON schema, heuristic fallback for extraction
  classifier.py  Classify orchestration: text -> LLM (or heuristic)
  samples.py     Built-in sample customer messages
  schemas.py     Pydantic models (Invoice, Classification, WordBox, ...)
static/
  index.html     UI shell with mode nav (Extract / Classify)
  app.js         Both tools' frontend logic + PDF.js + mode switching
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

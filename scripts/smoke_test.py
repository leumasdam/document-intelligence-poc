"""End-to-end smoke test — exercises all three tools + the integration path.

Usage:  python scripts/smoke_test.py [base_url]
        (base_url defaults to http://127.0.0.1:8000)

Exits non-zero on the first failed check, so it doubles as a CI gate.
"""
import json
import pathlib
import sys
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"

passed = 0
failed = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    mark = "PASS" if condition else "FAIL"
    if condition:
        passed += 1
    else:
        failed += 1
    print(f"  [{mark}] {label}" + (f" — {detail}" if detail else ""))


def post_json(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def post_pdf(path: str, pdf_path: pathlib.Path) -> dict:
    boundary = uuid.uuid4().hex
    body = b"".join([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{pdf_path.name}"\r\n'.encode(),
        b"Content-Type: application/pdf\r\n\r\n",
        pdf_path.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


print(f"Smoke test against {BASE}\n")

# 1. Extract
print("Extract (PDF -> structured JSON)")
ex = post_pdf("/extract", ROOT / "sample-data" / "claim-form.pdf")
check("document_type detected", ex["invoice"]["document_type"] == "claim_form",
      ex["invoice"]["document_type"])
check("total extracted", ex["invoice"]["total"] is not None, str(ex["invoice"]["total"]))
check("line items found", len(ex["invoice"]["line_items"]) > 0,
      f'{len(ex["invoice"]["line_items"])} items')
check("word boxes returned", len(ex["word_boxes"]) > 0, f'{len(ex["word_boxes"])} boxes')

# 2. Classify
print("\nClassify (text -> category + priority + team)")
cl = post_json("/classify", {
    "text": "Dobry den, uz druhy mesiac cakam na vyplatu plnenia. Obratim sa na NBS a SOI.",
})
check("category assigned", bool(cl["classification"]["category"]),
      cl["classification"]["category"])
check("high priority on regulatory threat", cl["classification"]["priority"] == "high",
      cl["classification"]["priority"])
check("routing team set", bool(cl["classification"]["route_to"]),
      cl["classification"]["route_to"])

# 3. Summarize
print("\nSummarize (long narrative -> summary + draft)")
sm = post_json("/summarize", {
    "text": "Dobry den, pisem ohladom skody na streche po burke z 12.5.2026. "
            "Poskodenych je 30 skridiel, zatekala voda do podkrovia. "
            "Zmluva MAJ-55 44 33 22 11. Cakam uz dlho, je to neprijemne. Dakujem.",
})
check("executive summary present", len(sm["summary"]["executive_summary"]) > 20)
check("key facts extracted", len(sm["summary"]["key_facts"]) > 0,
      f'{len(sm["summary"]["key_facts"])} facts')
check("response draft generated", len(sm["summary"]["customer_response_draft"]) > 40)
check("sentiment detected", sm["summary"]["sentiment"] in
      {"satisfied", "neutral", "frustrated", "angry"}, sm["summary"]["sentiment"])

# 4. Integration
print("\nIntegration (POST /integrate)")
ig = post_json("/integrate", {
    "kind": "classification",
    "payload": cl["classification"],
})
check("case id generated", ig["case_id"].startswith("CR-"), ig["case_id"])
check("recipient routed", "@" in ig["recipient_email"], ig["recipient_email"])
check("webhook status reported", ig["webhook_status"] in
      {"delivered", "failed", "not_configured"}, ig["webhook_status"])

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)

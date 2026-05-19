"""Smoke test: POST sample claim form to the running server."""
import json
import pathlib
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
pdf = (ROOT / "sample-data" / "claim-form.pdf").read_bytes()
boundary = uuid.uuid4().hex
body = b"".join(
    [
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="file"; filename="claim-form.pdf"\r\n',
        b"Content-Type: application/pdf\r\n\r\n",
        pdf,
        f"\r\n--{boundary}--\r\n".encode(),
    ]
)
req = urllib.request.Request(
    "http://127.0.0.1:8000/extract",
    data=body,
    method="POST",
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
resp = urllib.request.urlopen(req, timeout=30)
payload = json.loads(resp.read())
print(f"mode:         {payload['mode']}")
print(f"document_type: {payload['invoice']['document_type']}")
print(f"policy_number: {payload['invoice']['policy_number']}")
print(f"incident_date: {payload['invoice']['incident_date']}")
print(f"total:         {payload['invoice']['total']}")
print(f"line_items:    {len(payload['invoice']['line_items'])}")
print(f"word_boxes:    {len(payload['word_boxes'])}")
print(f"pages:         {len(payload['pages'])}")
print(f"pdf_base64:    {len(payload['pdf_base64'])} chars")
print(f"missing:       {payload['invoice']['missing_fields']}")

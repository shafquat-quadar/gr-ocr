# GR Agent POC — OCR-Based SAP Goods Receipt Agent

## Overview

A local, deterministic proof-of-concept that lets a warehouse operator photograph a package/label, automatically extracts goods-receipt fields via Tesseract OCR and regex, validates them against SAP purchase-order data, and (after human confirmation) posts a goods receipt to SAP — or records it against mock data in local JSON files.

No LLM, no agent framework. Fully runnable locally in Docker.

---

## Architecture

```
Image → ImageService → OCRService (Tesseract) → ParserService (regex)
      → MatchingService (PO item matching, rapidfuzz)
      → ValidationService (rule-based guardrails)
      → GROrchestrator (state machine + audit trail in SQLite)
      → SAPAdapter  ──→  MockSAPAdapter  (JSON files)
                    └──→  RealSAPODataAdapter  (httpx + CSRF)
```

Status machine:

```
CREATED → IMAGE_UPLOADED → OCR_COMPLETED → PARSING_COMPLETED
        → NEEDS_CORRECTION ←→ VALIDATED → READY_FOR_CONFIRMATION
        → POSTING_IN_PROGRESS → POSTED | FAILED
        NEEDS_CORRECTION | VALIDATED | READY_FOR_CONFIRMATION → REJECTED | BLOCKED
```

---

## Local Setup

### Prerequisites

- Docker >= 24
- docker compose >= 2

### Run

```bash
git clone <repo>
cd gr-ocr
cp .env.example .env
docker compose up --build
```

Swagger UI: http://localhost:8000/docs

---

## Mock Mode Usage (default)

`SAP_MODE=mock` is the default. No SAP credentials required.

The mock adapter reads PO data from `app/data/mock_purchase_orders.json` and writes material documents to `app/data/mock_material_documents.json`.

### End-to-End Flow

1. **Upload image**
   ```
   POST /api/v1/gr/drafts
   Content-Type: multipart/form-data
   file=@label.jpg
   ```

2. **Review draft**
   ```
   GET /api/v1/gr/drafts/{request_id}
   ```

3. **Correct if needed**
   ```
   PATCH /api/v1/gr/drafts/{request_id}
   {"quantity": 10, "entry_unit": "EA", "batch": "B24X91"}
   ```

4. **Revalidate**
   ```
   POST /api/v1/gr/drafts/{request_id}/validate
   ```

5. **Confirm (post)**
   ```
   POST /api/v1/gr/drafts/{request_id}/confirm
   {"confirmed_by": "user@example.com", "posting_date": "2026-05-21"}
   ```

6. **View audit trail**
   ```
   GET /api/v1/gr/drafts/{request_id}/audit
   ```

---

## Real SAP Mode

Set in `.env`:

```
SAP_MODE=real
SAP_AUTH_TYPE=basic          # or bearer
SAP_BASE_URL=https://your-sap-host.example.com/sap/opu/odata/sap
SAP_CLIENT=100
SAP_USER=YOUR_USER
SAP_PASSWORD=YOUR_PASSWORD   # not logged
# or for bearer:
SAP_BEARER_TOKEN=YOUR_TOKEN  # not logged
SAP_VERIFY_SSL=false
SAP_TIMEOUT_SECONDS=60
```

The real adapter calls:

- `GET .../API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder('{po}')?$expand=to_PurchaseOrderItem`
- `POST .../API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader`
- CSRF token is fetched with `X-CSRF-Token: Fetch` before every POST
- Cookies are reused in the same httpx.Client session
- 403 CSRF failures trigger one automatic token refresh and retry

No credentials, bearer tokens, CSRF tokens, or cookies are ever logged.

---

## Sample Label Test Cases

Create a plain-text image (e.g. using ImageMagick: `convert -size 400x200 xc:white -font Courier -pointsize 18 -fill black -annotate +20+40 "$(cat label.txt)" label.png`) with each label below.

### Label 1 — Happy Path

```
PO: 4500166595
QTY: 10 EA
LOT: B24X91
PRESSURE SENSOR ASSEMBLY
```

Expected: `READY_FOR_CONFIRMATION`, `can_post=true`, matched item `00010`

### Label 2 — Missing Batch (batch required)

```
PO: 4500166595
QTY: 10 EA
PRESSURE SENSOR ASSEMBLY
```

Expected: `NEEDS_CORRECTION`, `can_post=false`, error `BATCH_REQUIRED_MISSING`

### Label 3 — Quantity Exceeds Open Quantity

```
PO: 4500166595
QTY: 50 EA
LOT: B24X91
```

Expected: `BLOCKED`, `can_post=false`, error `QUANTITY_EXCEEDS_OPEN_QTY`

### Label 4 — Multi-Item PO, No Item Hint

```
PO: 4500166596
QTY: 10 EA
```

Expected: `NEEDS_CORRECTION`, `can_post=false`, `candidate_items` returned

### Label 5 — Serial Required, Insufficient Serials

```
PO: 4500166597
QTY: 2 EA
SN: SN10001
```

Expected: `NEEDS_CORRECTION`, `can_post=false`, error `SERIAL_COUNT_MISMATCH`

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SAP_MODE` | `mock` | `mock` or `real` |
| `SAP_AUTH_TYPE` | `basic` | `basic` or `bearer` |
| `SAP_BASE_URL` | — | Required when `real` |
| `SAP_CLIENT` | `100` | SAP client code |
| `SAP_USER` | — | Required for basic auth |
| `SAP_PASSWORD` | — | Required for basic auth |
| `SAP_BEARER_TOKEN` | — | Required for bearer auth |
| `SAP_VERIFY_SSL` | `false` | Verify SAP TLS cert |
| `SAP_TIMEOUT_SECONDS` | `60` | HTTP timeout |
| `DATABASE_URL` | `sqlite:///./db/gr_agent.sqlite` | SQLite path |
| `UPLOAD_DIR` | `./uploads` | Image storage directory |
| `MAX_UPLOAD_MB` | `10` | Max image upload size |
| `ALLOWED_IMAGE_TYPES` | `image/jpeg,image/png` | Allowed MIME types |
| `REQUIRE_HUMAN_CONFIRMATION` | `true` | Always require confirm step |

---

## Running Tests

```bash
# Inside container
docker compose exec gr-agent pytest tests/ -v

# Locally (requires Tesseract + Python 3.11)
pip install -r requirements.txt
pytest tests/ -v
```

---

## Known MVP Limitations

- `batch_required` and `serial_required` flags default to `false` for real SAP mode (not derivable from PO OData without material master lookup).
- No multi-item GR (one PO item per request).
- No OAuth / BTP principal propagation.
- No multi-tenant isolation.
- Single-node SQLite — not suitable for horizontal scaling.
- OCR confidence scores not available per-character from pytesseract without `image_to_data`.

## Production Hardening Backlog

- Derive `batch_required`/`serial_required` from SAP material master or classification system.
- Replace SQLite with PostgreSQL for concurrent access.
- Add OAuth2/BTP principal propagation for real SAP calls.
- Add per-request audit log retention policy.
- Add async workers for OCR (long-running jobs).
- Add structured logging with correlation IDs.
- Implement rate limiting and request authentication.
- Container image scanning and non-root user in Dockerfile.

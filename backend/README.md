# KHUTA backend

This FastAPI service uses the existing PostgreSQL database `islamic`. `public.passages` remains the source of truth and is read-only to this application. The five demo stations have 30 validated controlled-content rows, 112 provenance records, and 19 station-to-passage links. Do not run corpus ingestion or embedding jobs as part of the demo setup.

## Current database architecture

- `public.passages`: 166,774 existing records. The integration tests verify this count and compare the controlled station content against the approved report.
- `app.embeddings`: existing `vector(1536)` schema and HNSW cosine index; currently zero vector rows. Configuration remains `text-embedding-3-small` / 1536 dimensions. No embeddings were created by this integration.
- `app.content_sources`: 30 source/type registry entries; current source verification and rights state still require review. Generic religious retrieval remains blocked until eligible sources are explicitly verified and approved.
- `app.media_assets`: additive registry, currently empty. The API serves only records with `verification_status=verified` and `rights_status=permitted`.
- Governance Level 3 remains disabled. Personal-fatwa questions return a human referral.

## Run locally

Use the existing database connection through local environment configuration; never commit credentials. Required database driver dependencies are in `requirements.txt`. The API starts with the real AI provider optional and returns controlled fallback content when generation is unavailable.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Set DATABASE_URL to the existing `islamic` database. Keep credentials in this ignored file.
uvicorn app.api:app --host 127.0.0.1 --port 8000
```

The application and Alembic load `backend/.env` with `python-dotenv`; an exported environment variable takes precedence. The API can start without a database URL, but database-backed routes return HTTP 503 until it is configured. Alembic uses the same settings through `migrations/env.py`; no one-off migration runner is needed:

```powershell
alembic current
alembic heads
# Only when a schema change is intentionally approved:
alembic upgrade head
```

Do not run ingestion as routine setup. Migration `0004_media_request_key` is additive and has already been applied to the previously verified database; it adds an optional interaction request key and the empty media registry. Do not run `load_to_db.py` or `app.scripts.ingest_data` for this demo.

## Shared card flow

The browser simulator and a future RFID/NFC adapter call the same backend service, `process_station_tap(card_id, station_code)`. The service checks visitor consent/expiry, reads the stored language and level, loads station content and mapped database evidence, applies source eligibility, generates only from retrieved evidence when the configured provider is available, stores the interaction, and returns screen-ready citations, crowding, and a recommendation. `request_id` supports idempotent reader retries.

Main routes:

- `POST /visitors` — create an opted-in demo visitor.
- `POST /taps` — run the shared simulated/RFID station-tap flow.
- `POST /ask` — retrieve and answer from governed evidence; unsupported or insufficient requests abstain.
- `POST /interactions/{id}/duration` and `GET /visitors/{card_id}/summary` — retain the existing interaction contracts.
- `DELETE /visitors/{card_id}` and `GET /app` — retain visitor deletion and demo screen contracts.
- `GET /health` — includes database and provider configuration status.

Generated Quran/Hadith quotations are never sourced from model memory. The quote and citation must come from retrieved PostgreSQL rows and pass source/reference validation. English translations are withheld from display until the corresponding source is verified and approved. Development traces include retrieved IDs, source governance state, provider/model configuration, and latency; production responses omit those traces.

## Tests and evaluation

Run unit tests with `python -m pytest -q tests`. The optional database integration test requires `KHUTA_DB_INTEGRATION=1` and `DATABASE_URL` configured in `backend/.env` or the environment. It creates and then removes only its own temporary visitor and interaction records.

The 58-case evaluation dataset is a development/regression suite, not an independent held-out benchmark. Evaluate against the running API with `python evaluation/evaluate_ai.py --api-url http://127.0.0.1:8000 --results-dir evaluation/results/post_integration`. Groundedness, hallucination rate, and language quality require human review; they must not be inferred from retrieval scores.

See `../docs/RFID_INTEGRATION.md` and `../docs/MEDIA_SOURCES.md` for the reader and media contracts.

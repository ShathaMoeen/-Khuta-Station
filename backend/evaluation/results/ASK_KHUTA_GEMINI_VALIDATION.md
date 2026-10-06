# Ask KHUTA Gemini Grounded Generation Validation

Date: 2026-10-06

## Scope and result

The Ask generation change is implemented and covered by tests. Live database-backed validation could not complete because the configured PostgreSQL endpoint (`localhost:5433`) actively refused the connection. The API request failed while resolving the database-backed visitor/profile path, before retrieval and before provider construction. No Gemini request was sent.

## Code changes

- `app/api.py`: removed the Ask-only hard block on `verification_status` and `rights_status`. Gemini eligibility now requires configured AI plus non-empty local evidence with passage ID, text, source, and reference; the calling path obtains that evidence only through `_content_evidence`, which verifies its stored provenance and source/reference mapping. The database metadata is not changed.
- `app/api.py`: accepts only model-selected passage IDs that exist in the retrieved context and whose source/reference/text match. It reconstructs final citations from those local evidence rows, so provider-supplied URLs and citation labels are not trusted.
- `app/ai.py`: the Gemini instructions explicitly require answers to use only supplied evidence, prohibit model-memory religious claims and personal fatwas, require abstention when evidence is insufficient, and prohibit claiming sources are verified or rights-cleared.
- `tests/test_final_delivery.py`: tests reviewed registry metadata permitting use of controlled evidence, empty evidence, generated citations rebuilt from local evidence, personal-fatwa referral before provider use, simulated provider 429 fallback, and normal station opening staying database-backed without a provider call.

## Generation gate

Old behavior required every evidence row to be `verified`, `permitted`, and Level 1 or Level 2 even after its provenance had passed the local content checks. That incorrectly prevented demo Ask from adapting retrieved local evidence.

New behavior retains the classification/governance route, validates the local content-to-passage provenance, requires evidence fields and configured AI, and only then permits generation. `unverified` and `needs_review` remain unchanged metadata; they do not alone block this specific controlled Ask flow. No-evidence questions do not invoke Gemini. Personal fatwa requests are referred before the provider path.

## Provider and live results

- Configured provider/model: `gemini` / `gemini-3.5-flash` (read from settings without reading or displaying the API key).
- Requested live question: `ما معنى التوحيد؟` at `TAWHEED-01`, visitor `DEMO-KHUTA-002`.
- `/ask` attempt: blocked during database connection to `localhost:5433` (`ConnectionRefusedError`); no retrieved evidence was available to pass to the provider.
- Gemini calls made: **0**. No live generated answer, citations, or retrieved passage IDs can be reported truthfully.
- Second supported live question: not run because the first request could not reach retrieval/provider.
- Unsupported live weather question and personal-fatwa live request: not run; local database-dependent route unavailable. Automated fatwa regression confirms referral with `ai_generated=false`, `referral=true`, and `escalation_required=true` without calling Gemini.
- 429 fallback: simulated provider `GeminiRateLimitError` test passes; it returns the exact stored station body and local citations with `ai_generated=false`. No real quota was consumed.

## Safety, citations, and station flow

- Tests verify fabricated citation title/URL metadata is discarded and final citation fields are rebuilt from the matched retrieved passage.
- Empty evidence keeps the database-backed fallback and does not instantiate the provider.
- Personal fatwa is referred before generation.
- The normal station opening function remains unchanged and contains no provider invocation; its regression check confirms `ai_generated=false` and `ai_status=database_content`.
- No frontend, migration, ingestion, station story, provenance, passage, embedding, source-registry, or database code was changed.

## Database integrity and tests

- No database write was issued. The live path failed before retrieval; table counts could not be independently re-read in this run.
- No migration, `load_to_db.py`, embedding generation, or story update was run.
- Focused tests: **14 passed**.
- Relevant suite (`tests`, excluding `tests/test_database_integration.py`): **63 passed, 1 skipped**. The skip is the existing optional database-dependent test.
- Database counts and content were not changed by this task; current counts were not independently verified because PostgreSQL was unavailable.

## Required follow-up

Start or restore the existing PostgreSQL service on `localhost:5433`, then repeat the two supported live `/ask` requests and the unsupported/fatwa live checks. Do not infer live Gemini success from unit tests.

**FAIL — live validation blocked by PostgreSQL connection refusal at localhost:5433**

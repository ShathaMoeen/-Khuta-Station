# KHUTA controlled embedding pilot report

## Compatibility guard correction

The pilot had an OpenAI-only hard-coded model allowlist. Since `gemini-embedding-2` was not in that list, it reported the model as unconfirmed even though the configured Gemini provider had already performed a real single-vector probe returning 1536 dimensions. The guard contradicted the provider's runtime verification.

The pilot now uses the selected provider's `probe_embedding()` method, requires that real result to equal 1536, and stops before the pilot batch or database transaction on mismatch. It no longer maintains a separate model compatibility list. The Gemini batch request also uses the model-specific `models/gemini-embedding-2:batchEmbedContents` endpoint. Gemini query embedding now uses the query task prefix separately from the passage/document prefix.

## Runtime and database result

| Check | Result |
|---|---:|
| Provider/model | Gemini / `gemini-embedding-2` |
| Real single-vector probe | 1536 dimensions |
| PostgreSQL vector column | `vector(1536)`; unchanged |
| Controlled links | 19; expected reference set unchanged |
| Unique controlled passages | 13 |
| Controlled embeddings inserted | 13 |
| Total rows in `app.embeddings` | 13 |
| Distinct controlled passage IDs embedded | 13 |
| Wrong vector dimensions | 0 |
| Duplicate `(content_id, chunk_index)` rows | 0 |
| Exact source text and source/reference/type mapping | Verified for all 13 rows |
| `public.passages` | 166,774; unchanged |

The controlled pilot was run a second time. It found all 13 existing controlled chunks, had zero new chunks to embed, and left `app.embeddings` at 13 rows. It did not send another embedding request or insert duplicate rows.

## Tests and evaluation readiness

- Gemini embedding adapter tests: **2 passed**.
- Full unit suite: **33 passed, 0 failed, 1 skipped** (optional DB integration test).
- Database integration suite: **1 passed, 0 failed** when enabled.
- Python compile check: passed.
- Controlled vector/hybrid retrieval evaluation: **Ready to run**; this pilot did not run that evaluation.

Database integration cleanup left visitors/interactions at their baseline counts of 10/7. No frontend files, station passage links, or `public.passages` rows were changed. No migration or `load_to_db.py` run occurred.

## Live RAG and RFID readiness follow-up

See [GEMINI_RAG_VALIDATION_REPORT.md](GEMINI_RAG_VALIDATION_REPORT.md) for the English vector retrieval diagnosis, corrected controlled retrieval metrics, live Gemini validation results, database integrity checks, and remaining blockers. The English vector retrieval filter defect is fixed, and the latest unit, database integration, and compile checks pass. The complete live Gemini answer matrix could not be completed because `generateContent` repeatedly returned HTTP 429. KHUTA is **NOT READY FOR RFID INTEGRATION** until the required real grounded answers, safety cases, personalization checks, and all three live station tap generations pass.

The latest validation harness run made one Gemini `generateContent` request: **0 succeeded, 1 returned HTTP 429 (`RESOURCE_EXHAUSTED`)**. Safe response inspection classified this as quota exhaustion, not per-minute rate limiting. The provider supplied an 84,743-second retry hint; the harness did not retry before it and deferred because it exceeds the bounded 300-second validation wait. No API key or raw provider response was logged. Outstanding scenarios are marked `NOT_TESTED_RATE_LIMIT` in the validation report. Read-only integrity checks confirmed 166,774 passages, 13 embeddings, and 19 controlled links. Tests: 35 passed/1 skipped, database integration 1 passed, compile check passed. Personal-fatwa deterministic referral remains passing.

Final readiness: **NOT READY FOR RFID INTEGRATION — BLOCKED ONLY BY GEMINI RATE LIMIT/QUOTA**.

# KHUTA Gemini Master Content Validation Report

**Date:** 2026-10-06  
**Scope:** Backend station presentation and personalization against installed `app.station_content`.  
**Provider:** Gemini (`gemini-3.5-flash`, configured locally; the API key was not read out or logged).  
**Overall status:** **PARTIAL — live Gemini quota/rate limiting prevented the requested matrix and adversarial validation.**

## Implementation flow inspected

- `POST /taps` and `POST /rfid/tap` resolve the visitor/station and call `process_station_tap`; `/stations/{station_id}/interact` delegates to the same flow.
- `process_station_tap` loads the consented visitor profile through `VisitorAnalyzerService`, including the existing language, level, previously visited stations and non-sensitive exhibition-topic interests.
- It selects one exact `app.station_content` row by station, language and level through `_curated_content`, then loads that row's `app.station_content_provenance` passages.
- `_content_evidence` validates that provenance resolves to existing, non-empty passages and matching source-registry name/type/ID. It accepts only exact references or the known display forms `Quran 96:1` → `96:1` and `Sahih al-Bukhari 3` → `bukhari:3`. Unrecognized reference changes fail closed.
- Only evidence with the existing Level 2 governance label (or existing exact controlled-source approval) is supplied to Gemini. The selected Master Content body, source note, language and level define the visitor answer's factual boundary. Crowd and recommendation data are returned separately and are not passed as religious facts.
- `GeminiProvider.generate_answer` enforces structured output, rejects unknown citation IDs and responses without citations, rejects verbatim Quran/Hadith quotations, and constructs citations from the retrieved records. `visitor_citation` removes internal record IDs and debug/ranking fields from visitor responses.
- Successful station output is stored as `app.generated_content` with kind `station_explanation`, model label and readable source records. It remains presentation output, not evidence. A Gemini/provider/grounding failure falls back to the selected Master Content body and its provenance citations.
- `POST /ask` resolves the profile, classifies the question, applies governance, then uses `RAGService` to retrieve evidence before generation. Personal fatwa requests are referred before Gemini; general Shariah questions remain referred while no exact Level 3 source is approved. RAG validates generated citation IDs/source/reference/text against retrieved rows.

## Changes made

- Updated `app/station_flow.py` so station presentation adapts the selected installed Master Content rather than composing a station story from a separate general model context. The selected content's own mapped evidence supplies the citations.
- Added strict provenance/source validation and narrow normalization for already-stored display-reference formats. No station content, passage, source registry, provenance, embedding, or station link was edited.
- Tightened the Gemini instruction in `app/ai.py`: presentation may simplify or adjust detail by level, but it may not add facts, scenes, chronology, rulings, interpretations, motives, dialogue, dates, miracles or emotional states. The selected language and existing level variants are used.
- Added safe HTTP 429 status handling (`gemini_rate_limited`) without logging response bodies or credentials.
- Added `aclose()` to `GeminiProvider` and close it at station/RAG request boundaries to avoid leaking one `httpx.AsyncClient` per live call.
- Added `evaluation/run_gemini_master_content_validation.py` for sequential, paced execution of the required 32 core cases and eight representative intermediate cases. It records test-created data counts and stops on HTTP 429. It does not delete test records.
- Added unit checks for accepted/rejected provenance reference forms in `tests/test_station_content_flow.py`.
- Preserved the API response fields and frontend behavior.

## Master Content and provenance check

| Check | Result |
|---|---:|
| Rows across the eight requested stations | 48 |
| Rows whose evidence/provenance passed the runtime check | 48 |
| Exact language and level variants available | 48/48 |
| Content, provenance, passages, and station links changed by this task | 0 |

During initial probing, the strict first version of the validator flagged Quran provenance strings with a `Quran ` prefix. The normalizer was narrowed to the matching stored surah/ayah coordinate and tested. A separate pre-existing WAHY-01 issue remains: its intermediate/advanced rows map a Muslim record stored as `muslim:403` to provenance text `Sahih Muslim 160`. This may reflect a numbering-system difference, but the records do not establish that equivalence. Those rows fail closed for Gemini; the database was not changed. This station is outside the requested eight-station matrix, but SEERAH remains independently validated against its own provenance rows.

The sources continue to carry their existing `unverified` / `needs_review` rights and verification metadata. No rights or scholarly-verification status was promoted.

## Live station-personalization matrix

The task calls for 32 Arabic/English beginner/advanced cases and representative intermediate cases. Three tap-path generations succeeded before repeated HTTP 429 responses stopped useful live validation. The trial harness then encountered the QURAN display-prefix mismatch before sending its next request; that validator defect has since been fixed. The 32-case matrix was not completed.

| Station | Arabic beginner | Arabic advanced | English beginner | English advanced |
|---|---|---|---|---|
| TAWHEED-01 | **PASS** — generated twice; exact content level/language and five mapped references | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT |
| KAABA-01 | **PASS** — generated; four mapped Quran references | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT — a direct provider recheck after a 60-second cooldown received HTTP 429 | NOT_TESTED_RATE_LIMIT |
| SALAH-01 | NOT_TESTED_RATE_LIMIT — tap returned safe Master Content fallback | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT |
| SEERAH-01 | NOT_TESTED_RATE_LIMIT — tap returned safe Master Content fallback | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT |
| HISTORY-01 | NOT_TESTED_RATE_LIMIT — tap returned safe Master Content fallback | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT |
| QURAN-01 | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT |
| WUDU-01 | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT |
| ZAKAT-01 | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT | NOT_TESTED_RATE_LIMIT |

**Intermediate cases:** Arabic/English on TAWHEED-01, KAABA-01, SEERAH-01 and HISTORY-01 were not tested live due to the same 429 block.  
**Level-difference comparison:** not tested. The available successful calls cover only beginner Arabic; no beginner/advanced comparison is claimed.  
**Adversarial station prompts:** KAABA dates/renovations, complete HISTORY timeline, personal WUDU ruling, exact ZAKAT calculation, and complete SEERAH biography were not tested live.  
**Language comparison:** only Arabic beginner was generated. English visitor-facing generation and language-specific adaptation remain unverified.

### Successful live examples

TAWHEED-01, Arabic beginner (Gemini returned non-empty content; citations matched the selected content provenance):

> يصف القرآن الكريم الله تعالى في سورة الإخلاص بأنه أحد. وتدعو آيات أخرى إلى عبادة الله وحده وتبيّن أنه خالق كل شيء، كما تذكر الآيات أهمية التوكل عليه وشكره.

Sources: `مصحف حفص`, Quran 112:1, 14:7, 2:163, 6:102 and 65:3. The same Arabic beginner content was generated in two independent taps with the same references.

KAABA-01, Arabic beginner:

> يذكر القرآن الكريم البيت الحرام في بكة، ويبين أن النبي إبراهيم والنبي إسماعيل عليهما السلام رفعا قواعد هذا البيت. كما يوجه القرآن إلى استقبال المسجد الحرام في الصلاة، ويربط البيت بعبادة الحج لمن استطاع إليه سبيلاً.

Sources: `مصحف حفص`, Quran 2:127, 2:144, 3:96 and 3:97. Both successful answers were non-empty and carried only readable source/reference citations; no passage IDs, vector scores or ranking data appeared in the visitor response. These examples do not establish full-matrix grounding or accuracy.

## Ask KHUTA, governance and citations

- **Personal-fatwa live test:** not sent to Gemini. Existing deterministic governance unit tests pass and route personal-fatwa requests to qualified human guidance.
- **Supported educational Ask:** not tested live in this task.
- **Unsupported question / general Shariah question:** not tested live in this task.
- **RAG citation validation:** inspected in `RAGService.answer`; existing unit tests verify a forged citation is withheld and stored source metadata is propagated. No new live Ask answer was produced for this report.
- **Generated station citation validation:** successful examples cited only evidence mapped to their selected Master Content rows. 429 fallback examples included the selected provenance citations.

## HTTP 429 and fallback

- `generateContent` attempts: **7** (one initial smoke tap, five matrix taps before the harness aborted, and one read-only provider recheck after a 60-second cooldown).
- Successful Gemini generations: **3**.
- HTTP 429 responses: **4**.
- Automatic retry attempts: **0**. The first matrix runner did not recognize the safe `gemini_rate_limited` status, so it proceeded through three 429 responses. The runner now stops at the first 429 and spaces requests by at least 15 seconds.
- The provider reports HTTP 429 as a safe status. One recheck after a 60-second cooldown also returned HTTP 429. The retry hint and API quota subtype were not captured during these calls, so this report does not claim whether the restriction was per-minute limiting or quota exhaustion.
- Each 429 station tap returned a non-empty controlled fallback with mapped citations. These are fallback passes, not live Gemini personalization passes.
- Gemini model metadata `GET` requests preceded generation calls; API key material and raw provider error bodies were not printed or retained in the report.

## Tests and shutdown finding

- Python compile checks: passed for changed application and validation files.
- Relevant non-destructive unit suite: **48 passed**, pytest exit code 0, 2.15 seconds.
- The database integration fixture was not run because it deletes the visitor rows it creates; that conflicts with preserving data during this task.
- The previously observed “passes but does not exit” pytest behavior did not reproduce in the repository's `.venv`. The current run exited cleanly. The precise cause of the earlier shutdown hang remains unconfirmed. A separate live-call resource issue was found and fixed by closing request-scoped Gemini clients in the station and RAG flows; this is not proof that it caused the earlier pytest hang.

## Database integrity

| Table | Before this task's live tests | After attempted validation |
|---|---:|---:|
| `public.passages` | 166,774 | 166,774 |
| `app.embeddings` | 13 | 13 |
| `app.stations` | 14 | 14 |
| `app.station_passages` | 58 | 58 |
| `app.station_content` | 75 | 75 |
| `app.station_content_provenance` | 280 | 280 |
| `app.visitors` | 11 | 18 |
| `app.interactions` | 8 | 14 |
| `app.generated_content` | 0 | 3 |

The seven visitor rows, six tap interactions and three generated presentations were created by these live test runs. They were retained; no existing visitor, interaction, or generated-content record was deleted. Trusted content/evidence counts remained unchanged.

## Verdict

**PARTIAL.** Station Master Content selection, provenance checks, Gemini grounding contract, visitor-level inputs, non-empty controlled fallback and safe citation shape are implemented. Three real Gemini station generations passed, but 429s blocked the remaining required live matrix, English/advanced/intermediate comparisons, adversarial cases and live Ask cases. Do not claim full personalization validation or 100% accuracy. Resume the runner after Gemini rate-limit/quota availability and resolve the WAHY-01 Muslim reference mapping separately before enabling those affected variants.

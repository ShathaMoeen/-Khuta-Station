# KHUTA Final Delivery Validation

Date: 2026-10-06

## 1. Final architecture

KHUTA now keeps the two paths separate:

- **Normal station opening:** visitor profile → station → exact `app.station_content` row for the visitor’s language and level → strict provenance validation → stored content and readable citations → recent-activity crowding estimate → recommendation. This path does not import or call an AI provider.
- **Ask KHUTA:** classify → apply safety/governance → resolve station and visitor context → load the exact installed content and its validated provenance when the station topic matches → generate only if source governance permits → validate returned citations. When Gemini is unavailable, the station-scoped path can return the exact stored content as a database-backed answer. Unsupported questions abstain; personal fatwa questions refer to a qualified person.

The visitor-facing station text is returned directly from the database. `personalized_explanation` exactly equaled the selected content body in the live tap check; `ai_generated=false`, `explanation_source=database`, and `ai_status=database_content`.

## 2. Final eight-station content inventory

The database has all **48/48** required variants: eight stations × Arabic/English × beginner/intermediate/advanced. Selection uses the exact station, language, and level; there is no fallback to another language or level.

| Station | Variants | Provenance rows | Linked evidence and factual support | Audit |
|---|---:|---:|---|---|
| TAWHEED-01 | 6 | 30 | Quran: 112:1, 14:7, 2:163, 6:102, 65:3. The text stays within oneness, worship, creation, reliance, and gratitude stated in those verses. | PASS |
| KAABA-01 | 6 | 24 | Quran: 2:127, 2:144, 3:96, 3:97. The text is limited to the House/foundations, qibla, Bakkah, and pilgrimage claims supported by these passages. | PASS |
| SALAH-01 | 6 | 30 | Quran: 2:43, 4:103, 11:114, 20:14, 29:45. Prayer, remembrance, prescribed times, and the stated effect are supported; the content disclaims detailed ritual/legal guidance. | PASS |
| SEERAH-01 | 6 | 30 | Quran: 3:123, 9:40, 96:1; Hadith: Bukhari 3 and 5807. It remains a limited journey overview and does not invent a broader chronology. | PASS |
| HISTORY-01 | 6 | 18 | Quran: 33:9, 33:22, 48:18. Content is limited to the confederates and the pledge under the tree described by the linked evidence. | PASS |
| QURAN-01 | 6 | 32 | Quran: 96:1–5; advanced variants also link Bukhari 3. Beginner/intermediate Quran-only text now describes the verses without claiming they alone establish the historical beginning of revelation. | PASS |
| WUDU-01 | 6 | 12 | Quran: 4:43, 5:6. Content describes what the verses mention and avoids asserting an unsupported legal interpretation of foot washing. | PASS |
| ZAKAT-01 | 6 | 24 | Quran: 2:43, 2:110, 9:60, 9:103. The text stays within the linked passages’ calls and stated recipient categories. | PASS |

All eight rows in this table cover Arabic and English and all three visitor levels. The read-only audit resolved every provenance record to a non-empty passage and matching source; it checked passage ID, source ID/name/type, station-content ID, and reference (including Quran coordinates). No random web sources or model memory were used for the story audit.

### Corrections made

- **QURAN-01:** corrected four Arabic/English beginner/intermediate rows to remove historical “beginning of revelation” claims that Quran 96:1–5 alone do not establish. The advanced rows retain the separately linked Bukhari 3 evidence.
- **WUDU-01:** corrected six rows to say the verse mentions the feet to the ankles; removed the ungrounded phrasing “washing the feet.”
- No other unsupported factual details were identified in the remaining 38 final-station variants during the evidence comparison.

Pre-edit snapshots are retained at [FINAL_DELIVERY_PRE_EDIT_BACKUP_20261006.json](FINAL_DELIVERY_PRE_EDIT_BACKUP_20261006.json) and [WUDU_CONTENT_PRE_EDIT_BACKUP_20261006.json](WUDU_CONTENT_PRE_EDIT_BACKUP_20261006.json).

## 3. Source metadata and trust status

Factual support and reuse rights are separate checks. No `verification_status`, `rights_status`, or `governance_level` was changed. All three source records used by these stories—`مصحف حفص` (Quran), `quranlab/hadith:bukhari-ar`, and `quranlab/hadith:muslim-ar`—remain `unverified` / `needs_review` / `APPROVED_LEVEL_2`. No license, rights clearance, or verification was fabricated.

Because the evidence rows do not currently meet the `verified` plus `permitted` gates, Ask KHUTA did not send them to Gemini. The database-backed station and Ask answers remain available with their actual citations. This report’s factual-support `PASS` does not mean copyright/reuse rights have been cleared; that registry review remains outstanding.

## 4. Exact provenance and WAHY regression

- All provenance links for the 48 final variants passed strict live-database checks: **280 provenance rows** in the complete installed table, with the final eight stations accounting for the per-station counts above.
- All six `WAHY-01` language/level variants also passed strict mapping checks.
- Canonical local Hadith reference `muslim:403` remains present and valid. It was not normalized to `Sahih Muslim 160`.
- Missing passages, mismatched references, and source mapping mismatches fail closed in the station-flow validator.

## 5. Normal station opening: live end-to-end check

The `DEMO-KHUTA-001` visitor opened TAWHEED-01, station ID 24, through `POST /stations/{station_id}/interact`.

- HTTP: **200**
- Profile: **Arabic, intermediate**, consent accepted
- Exact selected content: `app.station_content` Arabic/intermediate TAWHEED-01 row
- Returned body: byte-for-byte equal to the selected database body
- Readable sources: **5**, references **112:1, 14:7, 2:163, 6:102, 65:3**
- `ai_generated`: **false**; `explanation_source`: **database**; `ai_status`: **database_content**
- Gemini/provider call: **none**. For the live endpoint check, the provider factory was replaced with a function that raises if called; the request still completed successfully.
- Story and sources were non-empty. The public response contained readable references and attribution, not passage IDs, source IDs, scores, hashes, or ranking data.

Returned story:

> تعرض الآيات معاني محددة: يصف القرآن الله بأنه أحد، ويدعو إلى عبادته، ويذكره خالقًا لكل شيء. كما يرد ذكر التوكل والشكر في سياق آيتيهما.

The station recommendation was **QURAN-01**, an unvisited member of the normal eight-station pool. No experimental station was returned.

## 6. Ask KHUTA

### Classifier root cause and fix

Generic routing terms such as “station” / “محطة” could classify station-aware educational or story wording as general exhibition knowledge before the station-aware intent was considered. The classifier now retains personal-fatwa and general Shariah priority, then handles station-scoped educational/story intent before generic station routing. Topic aliases and station context route questions such as “What is Tawheed?” and “ما معنى التوحيد؟” to the installed station evidence.

### Exact live Arabic result

Request: `ما معنى التوحيد؟`, card `DEMO-KHUTA-001`, station `TAWHEED-01`.

- Classification/routing: supported station-scoped Islamic knowledge
- HTTP: **200**, status **answered**
- `ai_generated`: **false**; `referral`: **false**; `interaction_logged`: **false**
- Gemini status: **not invoked**. Current source verification/rights metadata does not meet the generation gate.
- Database fallback: **passed**, with the exact installed content and five validated citations.

Returned answer:

> تعرض الآيات معاني محددة: يصف القرآن الله بأنه أحد، ويدعو إلى عبادته، ويذكره خالقًا لكل شيء. كما يرد ذكر التوكل والشكر في سياق آيتيهما.

Readable sources: **مصحف حفص 112:1, 14:7, 2:163, 6:102, 65:3**. Citations matched the linked stored passages. The visitor response did not expose internal IDs or ranking diagnostics.

An English station-scoped Ask check (“What is Tawheed?”, English beginner) also returned the installed English story, `answered`, `ai_generated=false`, and the same five source references.

### Provider failure, abstention, and fatwa behavior

- The deterministic unit test simulated a Gemini HTTP 429 and verified that the validated database-backed answer and citations were returned (`ai_generated=false`). No live Gemini request was made for this source-governed Ask check.
- An unsupported Mars-weather question returned `insufficient_sources`, null answer, and no citations.
- `هل يجوز لي الطلاق في حالتي؟` returned `referral`, no answer, `ai_generated=false`, and `refer_to_qualified_guide_or_mufti`. It did not reach Gemini.
- Level 3 remains disabled; no source governance metadata was promoted.

## 7. Crowding audit

Crowding is a database-derived estimate, not a sensor reading. The SQL counts only interactions for the requested station whose `duration_s IS NULL` and whose `started_at` is within the configured recent window. Completed and stale interactions therefore stop contributing.

- Configured window: **5 minutes**
- Thresholds: **low < 3**, **medium 3–7**, **high ≥ 8** (the high threshold is configurable)
- Deterministic threshold and stale/completed-query regression tests: passed
- Live TAWHEED-01 response: **1** recent unresolved interaction, **low**
- Returned explanation: “Derived from recent unresolved interactions; no physical occupancy sensor is connected.”

## 8. Recommendation audit

The normal pool is restricted to TAWHEED-01, KAABA-01, SALAH-01, SEERAH-01, HISTORY-01, QURAN-01, WUDU-01, and ZAKAT-01. ST-01 and ST-02 remain in the database but are excluded. WAHY-01, HIJRAH-01, and BADR-01 are added only when the current station is SEERAH-01.

Candidates are filtered to unvisited stations and ranked by topic continuity first, then recent unresolved activity, then stable station ID. Thus crowding breaks ties between otherwise relevant candidates rather than overriding relevance. Unit tests verify the pool and ranking behavior; the live recommendation was QURAN-01.

## 9. Automated tests

- Non-destructive automated suite: **60 passed, 1 skipped**.
- Read-only database trust audit: **1 passed**, verifying all 48 variants, their provenance, the six WAHY variants, and core row counts.
- The destructive database integration fixture was not run because it inserts and deletes database fixtures; all tests run for this delivery were non-destructive.
- Two existing FastAPI `on_event` deprecation warnings were reported; no test failures.

## 10. Database integrity

| Table | Final rows | Expected |
|---|---:|---:|
| `public.passages` | 166,774 | 166,774 |
| `app.embeddings` | 13 | 13 |
| `app.stations` | 14 | 14 |
| `app.station_passages` | 58 | 58 |
| `app.station_content` | 75 | 75 |
| `app.station_content_provenance` | 280 | 280 |
| `app.interactions` | 20 | May increase through demo taps |

No passages, embeddings, station records, station-passage links, visitors, or interaction records were deleted or reloaded. The final tap used a stable idempotency key; replaying it did not duplicate the interaction. The only content changes were the ten evidence-bounded story corrections described above.

## Final verdict

PASS — READY FOR FRONTEND INTEGRATION

The audited story content is evidence-bounded, station opening is database-backed and independent of Gemini, station-scoped Ask has a validated database fallback, personal-fatwa handling refers safely, crowding and recommendation behavior pass, and all protected database counts match. Source registry verification/reuse-rights statuses remain unresolved and unchanged; this is reported separately and has not been represented as cleared.

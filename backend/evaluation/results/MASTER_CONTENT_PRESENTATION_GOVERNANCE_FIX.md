# KHUTA Master Content Presentation Governance Fix

**Verdict: PASS_WITH_RATE_LIMIT — governance fix verified, Gemini was reached, but the provider returned HTTP 429 and the controlled fallback worked.**

## Root cause and diagnosis

The reported `SOURCE_GOVERNANCE_BLOCKED` outcome is emitted when selected evidence exists but the station flow's `approved_evidence` list is empty. That coupled the installed station-presentation path to a source-eligibility predicate instead of having a separate decision for already-installed Master Content with exact, validated provenance. This was the design defect: presentation adaptation had no explicit station-only policy gate.

There is a source/runtime discrepancy worth preserving in the audit trail: in the checked pre-change `app/station_flow.py`, the old predicate also admitted any row with `governance_level='APPROVED_LEVEL_2'`. The live TAWHEED-01 provenance records currently have that governance level, so the reported historical block cannot be reproduced from that exact source snapshot and current database state. The historic response likely came from a different or stale running revision; that explanation is an inference, not confirmed evidence. The replacement gate is independent of this ambiguity and was verified through the current runtime path.

For the exact selected TAWHEED-01 Arabic intermediate content row (station 24, content row 40), the five provenance records map to existing passages with matching references and source IDs. The source is ID 30, `مصحف حفص`; its current registry values are `governance_level=APPROVED_LEVEL_2`, `verification_status=unverified`, and `rights_status=needs_review`. Those registry values were not modified or promoted.

## Code changes and behavior

- `app/station_flow.py`: added `master_content_presentation_allowed`, requiring a normal station-presentation request, one of the eight scoped installed stations, the exact station/content/language/level match, non-empty installed text, and a non-empty set of passages whose references, passage IDs, source IDs, source names, and source types pass strict provenance validation. The exact validated Master Content evidence is the only evidence sent to the adapter.
- `app/station_flow.py`: added provider-failure containment. Provider errors, including Gemini 429, yield no generated answer and preserve the selected controlled Master Content fallback and its readable provenance citations.
- `app/station_flow.py`: added provenance row and passage ID consistency checks to `_content_evidence`.
- `app/ai.py`: kept the shared Ask/RAG instructions intact; the explicit complete-factual-boundary language is appended only when the station flow supplies its installed Master Content context.
- `app/api.py`: kept the RFID tap endpoint on its pre-existing non-adaptation behavior. No hardware behavior or integration was added.
- `tests/test_station_content_flow.py`: added positive, negative, status-preservation, scope and provider-failure tests.

The presentation exception does not use a global demo bypass, change source registry fields, change `RAGService`, alter `/ask` source filters, enable Level 3, or change personal-fatwa handling. An arbitrary passage without exact Master Content provenance cannot pass this gate.

## Station scope and gate verification

A read-only database sweep validated every exact language and visitor-level variant for these eight scoped stations: TAWHEED-01, KAABA-01, SALAH-01, SEERAH-01, HISTORY-01, QURAN-01, WUDU-01, and ZAKAT-01. **48 of 48** Arabic/English × beginner/intermediate/advanced selections had an exact content row, valid provenance, and a passing presentation gate.

Negative unit checks reject missing provenance, unvalidated evidence, reference mismatch, passage mismatch/nonexistent passage, source mapping mismatch, wrong station/content binding, wrong language or level, out-of-scope stations, and non-presentation requests. Open RAG governance regression tests passed. The pre-existing personal-fatwa referral and Level 3 approval tests passed. All six WAHY-01 variants continue to pass strict evidence validation with canonical local reference `muslim:403`; no `Sahih Muslim 160` normalization was introduced.

## Exact TAWHEED-01 live retest

Request: `POST /stations/24/interact`, card `GMC-E8963D0DF3395631`, Arabic, intermediate, station TAWHEED-01.

- HTTP response: **200**
- Correct station/profile/content selection: **PASS** — TAWHEED-01, Arabic, intermediate
- Provenance validation and presentation gate: **PASS** — content row 40, five exact mapped passages
- Gemini reached: **YES** — configured model metadata lookup returned HTTP 200
- Gemini generation: **HTTP 429 Too Many Requests**
- API result: `ai_generated=false`, `explanation_source=controlled_fallback`, `ai_status=gemini_rate_limited`
- Fallback and citations: **PASS** — installed Master Content remained available; visitor-facing sources were the actual Quran references `112:1`, `14:7`, `2:163`, `6:102`, and `65:3`. No passage IDs, source IDs, scores, or ranking diagnostics appeared in the response.

The exact fallback answer returned was:

> تعرض الآيات معاني محددة: يصف القرآن الله بأنه أحد، ويدعو إلى عبادته، ويذكره خالقًا لكل شيء. كما يرد ذكر التوكل والشكر في سياق آيتيهما.

An earlier attempt in this restricted execution environment failed with a network `ConnectError` before an HTTP response. After network access was granted, the live retry reached Gemini and returned the 429 above. The network error was not classified as a governance failure or a content-validation failure.

## Ask KHUTA and safety regression

No RAG retrieval policy, Ask route, source filters, or Level 3 allowlist was changed. `tests/test_rag_safety.py` and `tests/test_services.py` passed, including insufficient-evidence abstention, forged-citation rejection, personal-fatwa classification/referral behavior, and explicit Level 3 source-approval rules.

## Database integrity

Read-only checks after the live retest returned:

| Table | Rows |
|---|---:|
| `public.passages` | 166,774 |
| `app.embeddings` | 13 |
| `app.stations` | 14 |
| `app.station_passages` | 58 |
| `app.station_content` | 75 |
| `app.station_content_provenance` | 280 |

The source registry remains `unverified` / `needs_review` for the TAWHEED source. No passages, embeddings, source statuses, links, Master Content rows, migrations, or frontend files were changed. The two exact live API retests created interaction records; no existing visitors, interactions, or generated content were deleted.

## Tests

- Non-destructive automated suite: **54 passed** (`tests/`, excluding `test_database_integration.py`; that test deletes rows it creates, so it was not run under the instruction not to delete test rows).
- Python compilation: `app/station_flow.py`, `app/ai.py`, `app/api.py`, and `tests/test_station_content_flow.py` passed.
- `git diff --check`: passed.
- Read-only database validation: eight-station 48-variant gate sweep, six WAHY provenance variants, source status, and required table counts passed.

**Final verdict: PASS_WITH_RATE_LIMIT — governance fix verified, Gemini was reached, but the provider returned 429 and the controlled fallback worked.**

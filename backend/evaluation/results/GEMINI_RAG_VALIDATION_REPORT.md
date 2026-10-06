# Live Gemini RAG validation

Run time: 2026-10-06T01:32:04.903470+00:00 UTC.
Validation ran sequentially through KHUTA's normal `/ask` and `/taps` routes. The harness used temporary visitors and removed them afterward.

## Gemini rate-limit inspection and retry

- Gemini `generateContent` requests attempted: **2**
- HTTP 2xx generation requests: **0**
- HTTP 429 responses: **1**
- Retry attempts: **0** (maximum 2 per generation request).
- Retry hints observed: **1**; no retry hint: **0**; API error statuses: `{"RESOURCE_EXHAUSTED": 1}`.
- Retry hint delays in seconds: `[80875.0]`. Hinted waits up to 300 seconds are honored with at most one quota retry; longer hints are deferred rather than retried early.
- Retry delays: `[]` (Retry-After/RetryInfo honored when supplied; otherwise bounded exponential backoff).
- Safe 429 classification: `{"quota exhaustion": 1}`. API key headers and raw response bodies are not logged or written.

## Scenario results

- **AR Badr (previously verified): PASS**
- **AR first revelation: FAIL**
- **AR Hijrah: NOT_TESTED_RATE_LIMIT**
- **EN Badr: NOT_TESTED_RATE_LIMIT**
- **EN first revelation: NOT_TESTED_RATE_LIMIT**
- **EN Hijrah: NOT_TESTED_RATE_LIMIT**
- **AR semantic paraphrase: NOT_TESTED_RATE_LIMIT**
- **EN semantic paraphrase: NOT_TESTED_RATE_LIMIT**
- **Unsupported evidence: NOT_TESTED_RATE_LIMIT**
- **Incorrect Quran wording/reference: NOT_TESTED_RATE_LIMIT**
- **Personal fatwa deterministic referral: PASS**
- **Personalization ar_beginner: NOT_TESTED_RATE_LIMIT**
- **Personalization ar_advanced: NOT_TESTED_RATE_LIMIT**
- **Personalization en_beginner: NOT_TESTED_RATE_LIMIT**
- **Simulated tap BADR-01: NOT_TESTED_RATE_LIMIT**
- **Simulated tap WAHY-01: NOT_TESTED_RATE_LIMIT**
- **Simulated tap HIJRAH-01: NOT_TESTED_RATE_LIMIT**

## Knowledge responses and citations

### AR first revelation — FAIL

- API status: `ai_unavailable`; generated: `False`; stored citation check: `True`
- Question: ماذا حدث عندما بدأ نزول الوحي؟
- Answer: (no answer returned)
- Citations:
  - مصحف حفص — 96:5
  - مصحف حفص — 96:3
  - مصحف حفص — 96:1
  - مصحف حفص — 96:4
  - مصحف حفص — 96:2

### AR Hijrah — NOT_TESTED_RATE_LIMIT

- API status: `ai_unavailable`; generated: `False`; stored citation check: `True`
- Question: ماذا حدث أثناء الهجرة؟
- Answer: (no answer returned)
- Citations:
  - مصحف حفص — 9:40

### EN Badr — NOT_TESTED_RATE_LIMIT

- API status: `not returned`; generated: `False`; stored citation check: `False`
- Question: What happened at the Battle of Badr?
- Answer: (no answer returned)
- Citations:
  - None

### EN first revelation — NOT_TESTED_RATE_LIMIT

- API status: `not returned`; generated: `False`; stored citation check: `False`
- Question: What happened when the first revelation began?
- Answer: (no answer returned)
- Citations:
  - None

### EN Hijrah — NOT_TESTED_RATE_LIMIT

- API status: `not returned`; generated: `False`; stored citation check: `False`
- Question: What happened during the Hijrah?
- Answer: (no answer returned)
- Citations:
  - None

### AR semantic paraphrase — NOT_TESTED_RATE_LIMIT

- API status: `not returned`; generated: `False`; stored citation check: `False`
- Question: ما أول رسالة تلقّاها النبي في غار حراء، وما معناها العام؟
- Answer: (no answer returned)
- Citations:
  - None

### EN semantic paraphrase — NOT_TESTED_RATE_LIMIT

- API status: `not returned`; generated: `False`; stored citation check: `False`
- Question: Which early message is associated with the cave experience, and what does it emphasize?
- Answer: (no answer returned)
- Citations:
  - None

## Governance and unsupported evidence

- Personal fatwa: **PASS**; deterministic referral occurred before a Gemini generation request: `True`.
- Unsupported evidence: **NOT_TESTED_RATE_LIMIT**; API status `not returned`; answer: (no answer returned)
- Incorrect Quran wording/reference: **NOT_TESTED_RATE_LIMIT**; API status `not returned`; answer: (no answer returned)

## Personalization

### ar_beginner — NOT_TESTED_RATE_LIMIT

- Language/level: `not tested` / `not tested`; citations verified: `False`
- Answer: (not tested or no answer returned)
- References: 

### ar_advanced — NOT_TESTED_RATE_LIMIT

- Language/level: `not tested` / `not tested`; citations verified: `False`
- Answer: (not tested or no answer returned)
- References: 

### en_beginner — NOT_TESTED_RATE_LIMIT

- Language/level: `not tested` / `not tested`; citations verified: `False`
- Answer: (not tested or no answer returned)
- References: 

Identical source/reference sets across the three profiles: **False**.

## Simulated station taps

### BADR-01 — NOT_TESTED_RATE_LIMIT

- AI status: `not tested`; language/level: `not tested` / `not tested`; citations verified: `False`
- Visitor explanation: (not tested or no generated answer returned)
- Citations: 

### WAHY-01 — NOT_TESTED_RATE_LIMIT

- AI status: `not tested`; language/level: `not tested` / `not tested`; citations verified: `False`
- Visitor explanation: (not tested or no generated answer returned)
- Citations: 

### HIJRAH-01 — NOT_TESTED_RATE_LIMIT

- AI status: `not tested`; language/level: `not tested` / `not tested`; citations verified: `False`
- Visitor explanation: (not tested or no generated answer returned)
- Citations: 

## Visitor-output grounding/privacy checks

For successful Ask/tap answers, the application accepted only cited retrieved records; the harness checked every public source/reference against stored passages and checked exact quoted citation text. Public JSON was recursively checked for IDs, vectors, scores, ranks, hashes, governance diagnostics, model/provider data, and debug fields.

## Database integrity and automated checks

See the read-only database and test results recorded below after the harness run.

## Readiness

**NOT READY FOR RFID INTEGRATION**
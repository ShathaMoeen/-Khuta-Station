# KHUTA visitor experience validation

Date: 2026-10-06  
Scope: backend API and existing PostgreSQL database only. No frontend redesign, physical RFID hardware, passage changes, embedding writes, migration, or external data ingestion.

## Results

| Feature | Status | Evidence and limits |
|---|---|---|
| RFID UID registry audit | PASS | Existing `app.rfid_cards` records were used; test selected four active, unassigned rows without printing UIDs. Existing table already has a unique constraint on the stored UID. |
| RFID assignment | PASS | Added admin-authenticated `POST /rfid/assign`. It accepts only an existing active registry card and an existing, unexpired, consented visitor; repeat assignment to the same visitor is idempotent and assignment to another visitor returns HTTP 409. |
| RFID resolution | PASS | Added device-authenticated `POST /rfid/resolve`. It normalizes common UID separators, rejects malformed/unknown/unassigned/inactive/expired cards, fails closed on normalized collisions, and takes language/level from `app.visitors`, never the RFID row. |
| Simulated RFID tap | PASS | Added device-authenticated `POST /rfid/tap`; it resolves the UID and calls the existing `process_station_tap()` path. BADR was tested for Arabic beginner and English beginner/intermediate/advanced temporary profiles. |
| Visitor profile and consent | PASS | Tap results reflected temporary visitor language and level. Assignment rejected a temporary non-consented visitor with HTTP 403. Profile, journey-report, summary, and next-station endpoints now also reject visitors without active consent; the evaluator checked both allowed and denied paths. |
| Language personalization | PASS | Arabic and English controlled Badr content returned from the same station flow. An English visitor assigned to an RFID record whose stored tag language differs still received English, from the visitor profile. |
| Level personalization | PASS | English fallback text differed across beginner, intermediate, and advanced profiles. All three used the same complete set of controlled Badr passage references. This validates deterministic fallback personalization, not live model personalization. |
| Previous visits and interests | PARTIAL | The Arabic test visitor first tapped WAHY-01, then BADR-01; the Badr profile contained the prior station and observed topic. Live Gemini use of those fields to alter generated presentation remains unverified while generation is quota-blocked. |
| Crowding | PARTIAL | Tap response contained the existing estimate based on recent unresolved interactions. It is database-derived; no physical occupancy sensor is connected. |
| Station evidence and RAG retrieval | PASS | The station tap returned only supported BADR-01 linked evidence. The normal `/ask` route performed station-scoped lexical retrieval for the Badr story question and retrieved five records in each tested language. Vector/hybrid retrieval was not re-run by this simulation. |
| Visitor citations | PASS | Every returned source/reference pair was checked against the passages linked to BADR-01. The test found the same Quran references at all three English levels. Visitor responses omitted passage/source IDs, vector scores, debug/ranking data, and hashes. |
| Existing station interaction response | PASS | The simulation also called `POST /stations/{station_id}/interact`; current local response did not contain `interaction_id` or `station.id`. The pasted PowerShell sample showing those fields is inconsistent with the current local handler and should be checked against the server/process that produced it. |
| Unicode / encoding | PASS | API JSON response strings contained no U+FFFD replacement characters. Arabic text and typographic punctuation rendered correctly when evaluator stdout was explicitly UTF-8. The pasted `Ø...` / `Qurâan` text is consistent with terminal code-page decoding, not the current stored values/API response. |
| Duplicate tap protection | PASS | Replayed an identical tap request ID; the content matched and no second Badr interaction was inserted. |
| Question classification and governance | PASS | Normal `/ask` classified/retrieved the Badr story question. A personal-fatwa request returned deterministic `referral` before generation. An unsupported entrance-hours question returned `insufficient_sources`. |
| Story answer generation | PASS | After the prompt correction, live Gemini answered the English Badr story request for beginner and advanced profiles. Both outputs explicitly limited the scope to the retrieved verses; exact outputs are recorded below. |
| Gemini-generated visitor answers | PASS | Live embedding and generation requests succeeded for the two comparison profiles. A third beginner verification after tightening the mandatory scope sentence also passed. This is specific to the controlled Badr case, not the full scenario suite. |
| Next-station recommendation | PASS | Each Badr tap returned the normal next-station recommendation from journey and recent-interaction inputs, without exposing station database IDs. |
| Simulated end-to-end test | PASS | `python -m evaluation.test_visitor_experience` exercised temporary visitor creation, admin assignment, UID resolution, RFID tap, station evidence, citations, follow-up Ask retrieval, governance, and recommendation. Temporary visitors/interactions were removed and prior RFID mappings restored. |

## Tap pipeline inspected

`POST /stations/{station_id}/interact`, `POST /taps`, and the new `/rfid/tap` share `process_station_tap()`:

1. Resolve/load the station, then load the visitor profile and check active consent/expiry.
2. Load language, knowledge level, visited stations, and inferred exhibition topics from `app.visitors` and `app.interactions`.
3. Select controlled station content for the profile language/level.
4. Load source passages explicitly linked to that station through `app.station_passages`; approved translations are included only when source checks pass.
5. If AI is configured and approved evidence exists, request a grounded explanation. Otherwise return the level/language-specific controlled text fallback.
6. Persist one idempotent interaction (and generated content only after successful AI generation), then return readable citations, crowding estimate, and next-station recommendation.

Important limit: station taps retrieve the station’s explicitly linked evidence directly. They do not call the general `RAGService.retrieve()` ranking path. Follow-up `/ask` does use RAG. The evaluator exercised `/ask` with lexical retrieval while provider access was disabled, so it verified retrieval and citation plumbing but not Gemini answer quality.

## API and schema changes

- Added `app.rfid.canonical_rfid_uid()`, `resolve_rfid_visitor()`, and `assign_rfid_visitor()`.
- Added request schemas for RFID resolution, assignment, and tap.
- Added `POST /rfid/resolve` (device-authenticated), `POST /rfid/assign` (admin-authenticated), and `POST /rfid/tap` (device-authenticated).
- Added an active-consent gate to history-bearing visitor profile, summary, report, and recommendation endpoints while preserving their successful response shapes.
- No migration or table change was needed. Existing unique UID constraint is used; ambiguous normalized legacy UID values fail closed.
- `/rfid/tap` returns the existing visitor-facing station flow shape and does not return RFID UID or visitor `card_id`.
- No changes to frontend, passage, embedding, or station-passage records.

## Automated tests and database integrity

- Full backend suite including DB integration: **42 passed**.
- Warnings: 2 existing FastAPI `on_event` deprecation warnings; 1 pytest cache permission warning. No test failures.
- Database integration check: passed as part of that suite.
- Reversible live-DB evaluator: passed.
- Consent checks: consented profile/report/summary requests succeeded; non-consented reads/recommendation and assignment were rejected.
- Final counts after cleanup: `public.passages = 166,774`; `app.embeddings = 13`; `app.station_passages = 19`.
- RFID mappings were compared with the pre-run values and restored. Temporary test visitors and their interactions were deleted.
- No migrations were applied and no load/ingestion scripts ran.

## Remaining blockers

1. Broader live scenarios beyond the controlled English Badr story were not rerun in this task. This result does not certify all languages, stations, or question categories.
2. The current Badr comparison verifies source IDs/references via the API citation validator and human-reviewed the returned answers against those verses. Continue to treat other model outputs as unverified until similarly tested.
3. Crowd estimates are derived from interactions; physical crowd/occupancy integration remains absent.
4. Current station-content fallback source notes say rights status remains under review. The response correctly cites linked Quran evidence, but the fallback prose’s own publisher/rights provenance still needs review before broad production use.

## Local simulation command

From the `backend` directory, with the existing `backend/.env` database settings available:

```powershell
python -m evaluation.test_visitor_experience
```

The script uses temporary records, disables provider keys in its own process to avoid Gemini quota calls, and restores the database state it temporarily uses.

## Readiness

**PARTIAL** — the live English Badr beginner and advanced Ask cases now pass with the same trusted references, grounding limits, and readable citations. The previously observed provider quota failure is no longer blocking these calls. The wider scenario suite and physical RFID integration remain outside this validation.

## Live BADR RAG retest

Both completed requests used the existing `/ask` API with `station_code=BADR-01` and the question:

> Tell me the story of the Battle of Badr in a simple way.

### Runtime trace

| Stage | Result |
|---|---|
| Visitor profile resolution | PASS — `AI_TEST_001` resolved as English, beginner, with active consent. The advanced comparison used a temporary English advanced visitor, deleted after the request. |
| Question classification | PASS — `islamic_knowledge`; the classifier recognized “Badr”. |
| Station scoping | PASS — `BADR-01` resolved to station 12 and retrieval was scoped to its five controlled support links. |
| English-to-Arabic evidence | PASS — Gemini `gemini-embedding-2` created the English query vector; retrieval returned the linked Arabic Quran passages. Visitor language did not filter out Arabic evidence for this station. |
| Retrieved passage count | 5 per request |
| Retrieved references | Quran 3:123, 3:124, 3:125, 3:126, 3:127 |
| Evidence filtering | PASS — all five passed the existing controlled-station source/governance allowlist. |
| Gemini generation | PASS — `gemini-3.5-flash` returned `answered`, `ai_generated=true`, and a non-null response for both profiles. |
| Citation validation | PASS — every model-used source identifier matched retrieved evidence; the final visitor sources were the same five stored references in both answers. No internal IDs or ranking data appeared in the visitor response. |
| Beginner personalization | PASS — concise plain-language English; answer explicitly says the available verses do not establish a complete historical narrative or chronology. |
| Advanced personalization | PASS — more detailed structure and context, with an explicit limitation to the divine support/outcome described by those verses. |

The initial returned abstention was not caused by absent station evidence or an English-only filter. The runtime log from the successful comparison showed retrieval count 5 and Arabic source passages. Gemini had abstained because the previous generic instruction said to abstain when evidence was “insufficient” but did not distinguish no relevant evidence from relevant evidence that covers only part of a requested story. The shared provider instruction now directs it to answer only the supported part, explicitly state the scope limitation, and reserve `insufficient_sources` for evidence with no relevant support. It still forbids unsupported claims and unsupported religious quotations.

### Exact live beginner answer

> Based on the provided texts, God gave victory to the believers at the Battle of Badr when they were weak. To comfort them, they were promised help from thousands of angels if they stayed patient and mindful of God. This victory was meant to turn back those who disbelieved. Please note that the available sources only cover these specific divine aspects and do not provide a complete historical narrative or chronology of the battle's events.

### Exact live advanced answer

> Based on the provided sources, the story of the Battle of Badr is described through the lens of divine support and victory:
>
> * **Victory in Weakness:** God granted victory to the believers at Badr when they were weak and few in number, encouraging them to be mindful and grateful.
> * **Divine Reinforcement:** To reassure the believers, they were promised assistance from angels. This began with a promise of three thousand angels, which could increase to five thousand marked angels if the believers remained patient, stayed mindful of God, and faced a sudden attack.
> * **Reassurance and Purpose:** This support was sent as good tidings to bring peace to their hearts, emphasizing that true victory comes only from God. The ultimate purpose of this victory was to diminish the power of the disbelievers and turn them back disappointed.
>
> *Note: The provided sources focus specifically on the spiritual support and divine outcome of the battle, rather than providing a complete chronological or historical account of the military maneuvers and events leading up to the conflict.*

### Readable sources returned by both live answers

- **Quran — Aal-E-Imran 3:123** (stored source: مصحف حفص; attribution: Quranpedia.net, dump version 2026-10-03)
- **Quran — Aal-E-Imran 3:124** (stored source: مصحف حفص; attribution: Quranpedia.net, dump version 2026-10-03)
- **Quran — Aal-E-Imran 3:125** (stored source: مصحف حفص; attribution: Quranpedia.net, dump version 2026-10-03)
- **Quran — Aal-E-Imran 3:126** (stored source: مصحف حفص; attribution: Quranpedia.net, dump version 2026-10-03)
- **Quran — Aal-E-Imran 3:127** (stored source: مصحف حفص; attribution: Quranpedia.net, dump version 2026-10-03)

The API also returned `https://quranpedia.net` as the source URL. The controlled passage rows themselves contain Arabic Quran text; the English prose above is Gemini’s grounded explanation, not a stored English Quran translation.

Two comparison profiles completed successfully. A final beginner request was run after making the scope-limit instruction mandatory; it also passed. One earlier console capture could not print Arabic citation metadata under the default Windows stream encoding, so the response was repeated with UTF-8 output configured. No API key was printed. No passage, embedding, or station-passage data was modified.

Four Gemini `generateContent` requests returned HTTP 200 during this troubleshooting: the first successful response body was not captured because the Python console could not encode Arabic citation text, so the beginner check was repeated with UTF-8 configured; one advanced comparison followed; one final beginner check verified the mandatory scope sentence. A prior connection failure occurred before network access was granted and did not reach generation. No further live call is needed for this BADR check. After the final prompt edit, the targeted citation/RAG safety tests passed (9 passed); the full suite had passed immediately before this prompt-only edit (42 passed).

## Trusted personalized storytelling — live retest (2026-10-06)

**Result: PASS for the three requested BADR-01 profiles.** Tests used the normal `/visitors` and `/ask` routes against a freshly started backend process with Gemini enabled. Each request retrieved the five station-linked Arabic Quran passages and returned the same readable references: Quran 3:123–127 from `مصحف حفص` (attribution: `Quranpedia.net, dump version 2026-10-03`). All responses had `ai_generated=true`, `status=answered`, and `presentation_mode=storytelling`. Temporary visitor profiles were deleted after each request.

The first two checks sent to the already-running service on port 8001 returned abstentions because it had stale loaded application code. A freshly started service on port 8002 loaded the current code and passed. Review of early outputs also found overbroad phrasing and weak Arabic terminology. The Gemini instruction was tightened to preserve source conditions and quantifiers and to avoid unsupported emotional framing or mislabeling Quran-only evidence as a historical account.

### English beginner — exact final live answer

> The Support at Badr
>
> According to the Quran, during the Battle of Badr, the believers were in a weak position, but God granted them victory. The Quranic verses describe how the believers were comforted with the promise of divine help. They were asked if a reinforcement of three thousand angels would be enough for them. Furthermore, the Quran states that if they remained patient and mindful of God, and if the enemy attacked them suddenly, God would reinforce them with five thousand marked angels. This promise was given as good news to reassure their hearts, emphasizing that victory comes only from God. This support was intended to cut off a portion of those who disbelieved or to humiliate them so they would turn back disappointed.
>
> Please note that these Quranic sources only describe the spiritual reassurance and promised reinforcements for the believers; they do not establish the full historical timeline, the causes, or the complete sequence of events of the Battle of Badr.

### English advanced — exact final live answer

> ### The Divine Support at Badr
>
> According to Quranic accounts, the Battle of Badr was a pivotal event where the believers experienced profound divine assistance. The Quran highlights that God granted victory to the believers at Badr during a time when they were weak and few in number, urging them to remain mindful of God in order to show gratitude.
>
> During this encounter, the believers were comforted with the promise of spiritual reinforcement. The Quran recounts a reassurance given to them: that their Lord could reinforce them with three thousand sent-down angels. It further states that if they remained patient and conscious of God, and if the enemy suddenly rushed upon them, God would reinforce them with five thousand marked angels. This promised aid was sent as glad tidings to bring peace and reassurance to their hearts, emphasizing that true victory comes only from God, the Almighty and Wise. The intended outcome of this support was to cut off a portion of those who disbelieved or to suppress them so they would turn back in disappointment.
>
> *Please note that the available Quranic evidence only covers specific aspects of divine support and promises of angelic reinforcement during the battle; it does not establish a complete chronological narrative of the battle's physical events, the specific military strategies, the identities of all participants, or the political context leading up to the conflict.*

### Arabic beginner — exact final live answer

> يوم بدر والمدد الإلهي
>
> في يوم بدر، كان المسلمون في حالة ضعف وقلة عدد، ولكن الله سبحانه وتعالى نصرهم وأيدهم. يذكر القرآن الكريم أن الله بشر المؤمنين بمدد من الملائكة ليطمئن قلوبهم ويثبتهم؛ حيث كان هناك وعد بمدد من ثلاثة آلاف من الملائكة المنزَلين، ويمكن أن يصل إلى خمسة آلاف من الملائكة المسوّمين إذا صبر المؤمنون واتقوا وجاءهم الأعداء مسرعين. وكان هذا المدد الإلهي بشرى لقلوبهم لكي تطمئن، فالنصر الحقيقي لا يأتي إلا من عند الله العزيز الحكيم، لكي يقطع طرفاً من الذين كفروا أو يكبِتهم فيرجعوا خائبين.
>
> ونود الإشارة إلى أن المصادر المتاحة تركز فقط على جانب المدد الإلهي بالملائكة وبشرى النصر والهدف منه، ولا توضح التفاصيل التاريخية الكاملة للغزوة مثل أسبابها، أو أعداد الجيشين بالتفصيل، أو مجريات المعركة الميدانية الأخرى.

### Validation

- **RAG/citations: PASS.** All three came through `/ask`, returned Quran references 3:123, 3:124, 3:125, 3:126, and 3:127, and used the same trusted source. No internal IDs, scores, rankings, hashes, or developer metadata were exposed.
- **Grounding/evidence limits: PASS with a style caveat.** The answers disclose that the evidence is partial and avoid a full battle chronology. Advanced English uses interpretive descriptors (“pivotal,” “profound”) not stated verbatim in the verses; the concrete factual claims remain within the cited Quranic evidence.
- **Personalization: PASS.** Beginner English is concise, advanced English is more detailed, and Arabic is generated in Arabic. Their factual foundation and references are consistent.
- **Story mode/Gemini: PASS.** All three were live Gemini-generated responses, not a deterministic fallback, and used storytelling mode.
- **Focused automated tests: 13 passed** (`test_storytelling.py`, `test_citations.py`, `test_rag_safety.py`). Pytest showed a Windows cache-directory permission warning; the tests passed.
- **Read-only database check:** `public.passages=166,774`; `app.embeddings=13`; controlled `app.station_passages` links=19. No passage, embedding, or controlled link was modified.

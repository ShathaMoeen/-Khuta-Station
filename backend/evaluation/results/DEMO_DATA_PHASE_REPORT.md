# KHUTA controlled demo data phase report

Date: 2026-10-05  
Database: existing PostgreSQL database `islamic`  
Scope: additive source governance, five station drafts, provenance, chunking, and lexical retrieval. No new external content was imported.

## Database

| Measure | Before this phase | After this phase |
|---|---:|---:|
| `public.passages` | 166,774 | 166,774 |
| `app.content_sources` | 0 | 30 |
| `app.stations` | 2 | 7 (five demo stations added) |
| `app.station_content` | 3 | 33 (30 draft records added) |
| `app.station_passages` | absent | 32 exact links |
| `app.station_content_provenance` | absent | 192 provenance links |
| `app.visitors` | 10 | 10 (no demo visitors added) |
| `app.embeddings` | 0 | 0 |

`app.interactions` currently contains 7 rows; the earlier audit recorded 4. The demo preparation script did not insert interactions or visitor records. The added registry, station, content, mapping, and provenance data is idempotent: rerunning both source registration and demo preparation left the counts unchanged. No second database was created.

Alembic is at `0002_source_governance_demo`. The new migration only adds registry columns, check constraints, and the two provenance/mapping tables and indexes; migration `0001` was not edited. Neither migration upgrade modifies or deletes passage rows.

## Source governance

All 30 exact source/type pairs from `public.passages` are registered. Source names, types, source URLs, attribution values, and the existing registry metadata are preserved. Exact version dates were copied from attribution text where explicitly present; 12 rows have a parsed version and 18 do not.

| Status / metadata | Count |
|---|---:|
| `UNVERIFIED` / `unverified` / `needs_review` | 30 |
| Reviewed or verified | 0 |
| `permitted` or `restricted` rights decisions | 0 |
| Existing source URLs | 30 |
| Attribution present | 22 |
| Attribution missing | 8 |
| License or license URL missing | 30 |
| Publisher missing | 30 |
| Retrieval date missing | 30 |
| Verification evidence URL missing | 30 |
| Attribution requirement not established | 30 |

No license, publisher, attribution obligation, or permission was inferred. The source URL and attribution are retained as supplied by the passage records and have not been independently verified. `attribution_required` remains null because the database does not establish it. Quranpedia version strings found inside some attribution values remain provenance strings, not confirmation of licensing or authoritative version status.

## Demo content and references

The five stable codes have exactly six KHUTA-authored draft records each: Arabic and English at beginner, intermediate, and advanced levels. Existing two stations and three content records, including the earlier placeholders, were retained. Each new content record has provenance rows to exact existing source/type/reference/language records; all provenance remains `unverified` and `needs_review` pending human review.

| Station | References linked from existing passages |
|---|---|
| `QURAN-01` — القرآن الكريم | Qur’an/Hafs 1:1 and 96:1; matching Sahih International English translation records |
| `WAHY-01` — بداية الوحي | Qur’an/Hafs and matching English translation 96:1–5; Hadith record `bukhari:3` from `quranlab/hadith:bukhari-ar` |
| `HIJRAH-01` — الهجرة إلى المدينة | Qur’an/Hafs and matching English translation 2:218, 8:72, 9:40 |
| `BADR-01` — غزوة بدر | Qur’an/Hafs and matching English translation 3:123–127 |
| `HADITH-01` — السنة والحديث | Existing Hadith record `bukhari:3` from `quranlab/hadith:bukhari-ar` |

The summaries are deliberately bounded to what those stored records contain and do not reproduce external website paragraphs. “Bukhari no. 3” and the stored `sahih` grade are descriptions of current record metadata, not an independent authentication. The demo summaries are drafts until a qualified reviewer checks content and references. Production station delivery and exhibition retrieval now require provenance rows to be both `verified` and `permitted`; the development preview may display marked drafts for review.

## Chunking and retrieval

Chunking now treats Quran verses and their translations as atomic referenced records; keeps Hadith records complete and flags unusually long records for review; and splits Tafsir deterministically at paragraph/sentence boundaries. Generic long text uses deterministic word/sentence-aware chunks. Each chunk retains passage ID, source, reference, language, content type, visitor level, and chunk index. No chunks were embedded.

The Arabic lexical change keeps the existing PostgreSQL full-text candidates and adds an exact leading-phrase rank boost for excerpt-style questions. Arabic normalization now removes combining vowel marks without decomposing hamza letters; this matches the stored `text_norm` behavior better. When vectors exist, lexical and vector result lists are prepared for reciprocal-rank fusion with language/type/level/source filtering. Since `app.embeddings` is empty, the results below are lexical only, not hybrid.

The unchanged evaluation dataset has 58 cases. Same-case comparison:

| Metric | Prior lexical baseline | New lexical retrieval |
|---|---:|---:|
| Recall@1 | 0.400 | 0.425 |
| Recall@3 | 0.450 | 0.475 |
| Recall@5 | 0.450 | 0.500 |
| Arabic Recall@5 | 0.2692 | 0.3462 |
| Classification accuracy | 1.000 | 1.000 |
| Governance accuracy | 1.000 | 1.000 |

This is a measured retrieval gain on the same 58 cases, but overall Recall@5 remains 0.50 and Arabic Recall@5 remains 0.3462. Arabic search still uses PostgreSQL's `simple` full-text configuration, which does not provide Arabic morphology/stemming; more improvement needs a reviewed lexical design and, after credentials and approval, evaluation of the bounded vector pilot. Citation accuracy, answer correctness, hallucination rate, and answer language quality are `NOT_AVAILABLE`: there was no configured AI provider key and therefore no real generated answers to assess.

## Embedding pilot estimate

The five stations currently link **29 unique passages / 29 chunks**. The configured model is `text-embedding-3-small`; the existing vector column is `vector(1536)` and configured dimension is 1536. There is no valid provider credential, so the paid embedding request was skipped and `app.embeddings` remains empty. The ingestion script now requires explicit `--demo-stations`, an explicit limit from 1 to 500, and a configured key; it has no unbounded full-corpus embedding mode.

## Safety checks

- Backend suite: **19 passed**.
- Personal fatwa live pipeline check: classified as personal fatwa, escalated to qualified human guidance, and did not call the AI provider.
- General Shariah live pipeline check: Level 3 remained blocked. API eligibility now requires the requested exact source to have a registry row with `rights_status=permitted`, `verification_status=verified`, and `governance_level=APPROVED_LEVEL_3`. Unit tests confirm unverified, unpermitted, unrequested, or merely reviewed sources cannot unlock Level 3.
- Source registration and station/content/provenance generation were rerun; no duplicate records appeared.
- Passage count was read before and after the phase and remains exactly 166,774. No passage updates, deletes, truncations, embeddings, migrations of existing data, or dataset imports occurred.

## Remaining blockers and safe next steps

1. A qualified reviewer must verify the religious/historical facts and references in the 30 station drafts.
2. Rights review must identify the exact license, license URL, publisher, attribution terms, and permitted KHUTA use for every source before public distribution or embedding. Do not treat reputable status as reuse permission.
3. Add verification evidence, reviewer, and dates only when documented. Keep Level 3 disabled until the exact source has explicit approval.
4. Configure an authorized API key before the 29-passage embedding pilot or real answer/citation evaluation. The estimate, model, and dimension are recorded above; no paid call was made.
5. Improve Arabic retrieval further and rerun this same evaluation case set. Do not expand the dataset or attempt full-corpus embeddings in this phase.

KHUTA trusted demo data phase is blocked: human religious-fact and rights review are required before approving the demo sources.

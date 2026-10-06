# KHUTA Master Content Installation Report

**Date:** 2026-10-06  
**Scope:** Evidence-bounded installation for the requested visitor-facing stations.  
**Approval status:** Installed for demo use under the user's current task instruction. This is not independent scholarly verification or rights clearance.

> **Master Content is the factual source of truth. Future LLM output is presentation adaptation, not a new religious source.**

## Preflight and backup

Inspected live columns, nullability, defaults, identity/primary/foreign keys, unique constraints and status checks for `app.station_content`, `app.station_content_provenance`, `app.station_passages` and `app.content_sources` before writing. `station_content` requires `station_id`, `lang`, `level` and `body`; levels are constrained to `beginner`, `intermediate`, `advanced`. It has no approval/status field and no unique content key. `station_content_provenance` requires the content/source references and has a unique constraint on `(station_content_id, source_id, reference)` plus verification and rights status checks.

Pre-change backup: [MASTER_CONTENT_INSTALLATION_BACKUP_20261006.json](C:/Users/shada/Downloads/islamic-ai-challenge/backend/evaluation/results/MASTER_CONTENT_INSTALLATION_BACKUP_20261006.json). It contains all 33 `app.station_content` rows and all 112 `app.station_content_provenance` rows before the operation.

The existing content architecture selects by visitor language and level. For the seven stations without content, three presentation variants were installed for each of Arabic and English (six rows per station). Each level retains the same evidence map and factual claims; wording length and context vary. No per-level factual stories were created.

## What was installed

- **42 new `app.station_content` rows:** 7 stations × 2 languages × 3 levels.
- **168 new provenance rows:** one mapping per content row and each of its supporting source/reference records.
- **3 existing QURAN-01 English `source_note` fields were labelled** as visitor-facing educational adaptations, not authoritative Quran translations. Their titles, bodies and provenance were preserved.
- **No QURAN-01 content rows were added.** It already has six Arabic/English rows. The draft’s guidance/reflection paragraph depends on Quran 2:2, 17:9 and 38:29, which are not linked to QURAN-01. That paragraph was not installed; existing station links were not changed.

Arabic is the primary Master Content language. English titles and source notes identify the English text as an educational adaptation from Arabic. No English wording is represented as a stored authoritative Quran translation.

## Evidence validation

Before insertion, each new content evidence item was checked against `public.passages` by its specified passage ID. Type, language, exact stored reference, source and non-empty text were verified. Every Quran evidence item was also checked for a `supports` link to its own station. SEERAH-01 is the requested exception: it has no direct station links; its five provenance references resolve to supporting evidence linked to WAHY-01, HIJRAH-01 and BADR-01. No links were fabricated or changed.

KAABA-01 Quran 3:97 uses the corrected live record: **`22c982ca1b1d478ec600bd3f3ad310a70d4afbd5`** (`quran`, Arabic, `مصحف حفص`, reference `3:97`, non-empty text), linked to KAABA-01. The earlier truncated ID without the final `5` is not present in installed content or provenance.

For each of the 42 new content rows, the installed provenance set exactly matches the specified evidence passage IDs/references and source registry row. Every provenance passage exists and its passage reference matches the provenance reference. There are no content rows without provenance, duplicate content keys, duplicate provenance keys, or stale Quran 3:97 IDs in the installed rows.

## Station-by-station inventory

Every newly populated station has three Arabic rows and three English adaptation rows. The evidence count is the distinct passage count per station; provenance count covers all six level/language content rows.

| Station | Arabic present? | English adaptation present? | Supported evidence | Provenance rows | Content status and scope |
|---|---|---|---:|---:|---|
| TAWHEED-01 | Yes (3 levels) | Yes (3 levels) | 5 | 30 | EDUCATIONAL_ONLY — Quran-bounded oneness, worship, creation, reliance and gratitude. |
| KAABA-01 | Yes (3 levels) | Yes (3 levels) | 4 | 24 | EDUCATIONAL_ONLY — House, Ibrahim/Ismail foundations, Qiblah and Hajj connection; no architectural history. Includes verified Quran 3:97. |
| SALAH-01 | Yes (3 levels) | Yes (3 levels) | 5 | 30 | EDUCATIONAL_ONLY — prayer, remembrance, cited timing themes and stated effect; not a ritual or fiqh guide. |
| SEERAH-01 | Yes (3 levels) | Yes (3 levels) | 5 | 30 | PARTIAL — short journey hub pointing to the separate revelation, Hijrah and Badr stations; not a full biography or chronology. Direct station links remain zero. |
| HISTORY-01 | Yes (3 levels) | Yes (3 levels) | 3 | 18 | EDUCATIONAL_ONLY — limited Quranic event vignettes only; explicitly not a complete Islamic-history timeline. |
| QURAN-01 | Yes (3 existing levels) | Yes (3 existing levels; adaptation label added) | 6 existing provenance passages | 32 existing provenance rows | Existing bounded content preserved; no new Master Content row. The unlinked guidance/reflection draft paragraph was omitted. |
| WUDU-01 | Yes (3 levels) | Yes (3 levels) | 2 | 12 | EDUCATIONAL_ONLY — Quran-bounded explanation; no personal case or detailed fiqh guide. |
| ZAKAT-01 | Yes (3 levels) | Yes (3 levels) | 4 | 24 | EDUCATIONAL_ONLY — Quran-bounded overview and named recipient categories; no nisab, rates, personal calculations or eligibility ruling. |

The HISTORY-01 bodies state that their examples are limited and do not form a complete timeline/history. SEERAH-01 bodies are short orientation text only; their evidence points to specialized stations, and they do not repeat the WAHY/HIJRAH/BADR stories.

## Existing QURAN-01 content caveat

The six pre-existing QURAN-01 bodies were not changed. Their existing provenance records all resolve to passages with matching references. Five Quran references are linked directly to QURAN-01; the existing Bukhari 3 provenance used by its advanced rows is not a direct `station_passages` link. This pre-existing mismatch was left untouched to preserve controlled content and station links. The proposed new QURAN-01 guidance/reflection paragraph was also omitted because its Quran 2:2, 17:9 and 38:29 records are not linked to that station.

## Provenance and rights caveats

The provenance rows copy status and source URL from the live source registry; no publisher, license, retrieval date, verification or rights clearance was invented. Quran and Hadith evidence retain `verification_status=unverified` and `rights_status=needs_review`. Existing registry metadata may contain a governance level, but this does not establish independent scholarly verification or reuse rights. Rights-holder/license review and qualified source/text review remain outstanding. The English station content is a visitor-facing adaptation, not an authoritative translation.

The schema has no safe content approval field. Demo approval is documented here based on the current task instruction; no schema was changed and no religious dataset was marked scholarly verified. The source drafts retain their original DRAFT banner.

Personal worship cases, zakat calculations/eligibility, disputed fiqh and individual religious rulings are not answered by these Master Content bodies and must remain subject to governance referral to qualified human guidance.

## Before/after counts

| Table | Before | After |
|---|---:|---:|
| `app.station_content` | 33 | 75 |
| `app.station_content_provenance` | 112 | 280 |
| `public.passages` | 166,774 | 166,774 |
| `app.embeddings` | 13 | 13 |
| `app.stations` | 14 | 14 |
| `app.station_passages` | 58 | 58 |

All 112 pre-existing provenance rows match the backup. All 33 pre-existing content bodies/titles match the backup; the only existing-row changes are the three English QURAN-01 adaptation labels in `source_note`. Existing controlled content bodies remain unchanged.

## Idempotency

Ran `python -m app.scripts.install_master_content` twice. First run inserted **42 content rows** and **168 provenance rows**, and labelled the three existing English QURAN-01 notes. Second run inserted **0 content rows**, **0 provenance rows**, and made **0 note updates**.

The installer is [install_master_content.py](C:/Users/shada/Downloads/islamic-ai-challenge/backend/app/scripts/install_master_content.py). It validates the exact passages and applicable station links before writing, checks for conflicting existing content/provenance, and uses content keys plus the database provenance uniqueness constraint for repeatability.

## Tests

Ran the non-destructive backend unit modules (45 tests), excluding `tests/test_database_integration.py`. The test output displayed 45 passing progress markers and no failures, but the pytest process remained alive after the test progress completed and had to be interrupted; a clean pytest shutdown/exit status could not be confirmed. The database integration test was not run because its fixture inserts and then deletes visitor rows, which conflicts with the instruction not to delete visitor or interaction data. No live Gemini call was made.

## Required confirmations

- No Gemini/external LLM calls; no embeddings generated.
- No frontend, RFID, crowding or recommendation code changed.
- No passage rows, station rows, station-passage links, visitors or interactions changed.
- No migrations, destructive operations, truncation, or `load_to_db.py` run.
- Existing station content bodies and prior provenance were preserved; only the three English QURAN-01 source-note labels were added.
- Master Content was installed only in `app.station_content` with source-mapped `app.station_content_provenance`; it was not added to the passage corpus.

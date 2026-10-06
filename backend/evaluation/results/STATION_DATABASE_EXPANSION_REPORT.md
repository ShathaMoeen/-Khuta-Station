# KHUTA Station Database Expansion Report

**Date:** 2026-10-06  
**Operation:** Create seven missing visitor-facing stations and add only audited evidence links.  
**Result:** Seven stations were created with 38 verified links in the initial expansion. A coordinate-based Quran 3:97 lookup subsequently resolved the one omitted KAABA-01 link; one additional link was added. Final expansion total: 39 new evidence links. No content drafts were inserted.

## Pre-change schema and safeguards

Inspected the live PostgreSQL schemas via `information_schema.columns` and `pg_constraint`:

- `app.stations`: `id integer` primary key/sequence, `code text NOT NULL UNIQUE`, `name text NOT NULL`, `topic text NULL`, `location text NULL`, `created_at timestamptz DEFAULT now()`.
- `app.station_passages`: `id bigint` generated identity, `station_id integer NOT NULL`, `passage_id text NOT NULL`, `relationship_type text NOT NULL`, `priority numeric NULL` constrained to 0–1, `notes text NULL`, `created_at timestamptz DEFAULT now()`. Unique key is `(station_id, passage_id, relationship_type)`; foreign keys reference `app.stations` and `public.passages`.
- `app.station_content`: primary key, station foreign key, language and level required (defaults Arabic/beginner), optional title, required body, optional source note.
- `app.station_content_provenance`: generated data includes source/content foreign keys, reference, source URL, verification/rights status, retrieved date, notes, and optional passage ID; status check constraints apply.
- `app.content_sources`: source registry fields include required source key/name/type plus attribution, URL, metadata, publisher, license, rights and verification status, version/retrieval/verification fields.

Existing active exhibition stations use `Gallery A`, so the same location was used for all seven new stations. The specified Arabic names and topics were used directly. `station_passages` supports `supports` links at priority `1.0000`, with an exact source/reference note. The unique station-code constraint and `ON CONFLICT DO NOTHING`, combined with value checks on already-present target codes, make the seed repeatable without overwriting conflicting records.

The requested new station codes did not exist before the operation. `QURAN-01` existed and was not recreated. `ST-01`, `ST-02`, and all five existing controlled stations were not modified.

## Backup

Pre-change snapshot: [STATION_DATABASE_EXPANSION_BACKUP_20261006.json](C:/Users/shada/Downloads/islamic-ai-challenge/backend/evaluation/results/STATION_DATABASE_EXPANSION_BACKUP_20261006.json)

Created before any database writes. It contains all existing rows from `app.stations` (7), `app.station_passages` (19), `app.station_content` (33), `app.station_content_provenance` (112), and `app.content_sources` (30). The five table snapshots were later compared against the live database; every pre-existing row remained unchanged.

## Stations created

| ID | Code | Arabic name | Topic | Location | Evidence links |
|---:|---|---|---|---|---:|
| 24 | TAWHEED-01 | التوحيد | Tawheed | Gallery A | 11 |
| 25 | KAABA-01 | الكعبة | Kaaba | Gallery A | 10 |
| 26 | SALAH-01 | الصلاة | Prayer | Gallery A | 7 |
| 27 | SEERAH-01 | السيرة | Seerah | Gallery A | 0 |
| 28 | HISTORY-01 | التاريخ | Islamic History | Gallery A | 3 |
| 29 | WUDU-01 | الوضوء | Wudu | Gallery A | 2 |
| 30 | ZAKAT-01 | الزكاة | Zakat | Gallery A | 6 |

No column exists for a station description or safety scope. Accordingly, `HISTORY-01` retains the requested topic `Islamic History`; its boundary is documented here: **“Evidence-bounded Islamic historical/event vignettes.”** It must not be presented as a comprehensive history, chronology, or model-generated timeline. `SEERAH-01` is an overview/journey hub, not a replacement for WAHY-01, HIJRAH-01, or BADR-01. It has no links because the current schema does not require evidence links for a hub and the task directs against duplicating specialized links. No Prophet ﷺ depiction or relationship table was introduced.

## Evidence links inserted

All links use `relationship_type=supports`, priority `1.0000`. Before insertion, each supplied passage ID was checked for existence and its stored reference, type (`quran`), Arabic language and source against the existing Quran source baseline (`مصحف حفص`). No `public.passages` row was changed.

| Station | Quran references linked | Count |
|---|---|---:|
| TAWHEED-01 | 112:1, 112:2, 112:3, 112:4, 2:163, 6:102, 16:36, 21:25, 51:56, 65:3, 14:7 | 11 |
| KAABA-01 | 2:125, 2:127, 2:144, 3:96, 3:97, 22:26, 22:27, 22:28, 22:29, 14:37 | 10 |
| SALAH-01 | 2:43, 20:14, 4:103, 11:114, 17:78, 29:45, 2:110 | 7 |
| HISTORY-01 | 33:9, 33:22, 48:18 | 3 |
| WUDU-01 | 5:6, 4:43 | 2 |
| ZAKAT-01 | 2:43, 2:110, 9:60, 9:103, 9:71, 2:177 | 6 |
| **Initial expansion links** |  | **38** |
| **Quran 3:97 follow-up link** |  | **1** |
| **Total new expansion links** |  | **39** |

### Quran 3:97 ID discrepancy — resolved

The initial expansion report/seed data used the 39-character ID `22c982ca1b1d478ec600bd3f3ad310a70d4afbd` and incorrectly reported it absent. The live lookup by `type='quran'`, `surah=3`, `ayah=97` returned exactly one appropriate Arabic record. Its actual 40-character passage ID is `22c982ca1b1d478ec600bd3f3ad310a70d4afbd5` (the trailing `5` was missing in the earlier value). The single candidate has reference `3:97`, non-empty text, source `مصحف حفص`, and the same source as KAABA-01’s other Quran links. The previous audit document was not changed; this report corrects its stale/incorrect ID finding explicitly.

The verified row is linked to KAABA-01 as station-passage row ID `154`, using `relationship_type=supports`, priority `1.0000`. The earlier erroneous ID was not linked.

## Before/after database counts

| Table | Before | After |
|---|---:|---:|
| `public.passages` | 166,774 | 166,774 |
| `app.embeddings` | 13 | 13 |
| `app.stations` | 7 | 14 |
| `app.station_passages` | 19 | 57 after initial expansion; **58 final** |
| `app.station_content` | 33 | 33 |
| `app.station_content_provenance` | 112 | 112 |

The original controlled 19 station-passage rows were compared to the backup, including row IDs and stored fields; all remained unchanged. The prior 38 expansion links were also rechecked and remain unchanged. The seven existing station rows, all pre-existing station-content rows, provenance rows, and content-source rows match the backup. Exactly seven stations and 39 expansion links now exist.

## Idempotency

Ran `python -m app.scripts.create_expanded_stations` twice during the initial expansion. First run: 7 stations and 38 links inserted. Second run: 0 stations and 0 links inserted. For the focused Quran 3:97 operation, the first pass inserted 1 link and the second pass inserted 0. No duplicate station or station-passage link was created.

The repeatable operation is implemented in [create_expanded_stations.py](C:/Users/shada/Downloads/islamic-ai-challenge/backend/app/scripts/create_expanded_stations.py). Its KAABA-01 Quran 3:97 mapping now uses the verified 40-character passage ID. It does not overwrite pre-existing station fields and aborts if a target code exists with conflicting values.

## Regression verification

- Read-only `GET /stations` returned HTTP 200 with the existing response keys `code`, `id`, `location`, `name`, `topic`. Each protected station (`QURAN-01`, `WAHY-01`, `HIJRAH-01`, `BADR-01`, `HADITH-01`) appeared once. Their underlying rows and their links were unchanged.
- The non-database, non-Gemini unit tests displayed **45 passed** across the existing unit test modules. The pytest process remained alive after printing the completed test progress and did not exit cleanly; it was interrupted during shutdown. No assertion failure was printed, but a clean pytest exit status could not be verified.
- `tests/test_database_integration.py` was not run: it creates and then deletes visitor rows (with cascading interactions), conflicting with this task’s explicit prohibition on deleting visitor/interaction rows. No visitor or interaction test data was created by this task.
- No live Gemini request was made.

## Final confirmations

- Existing passages untouched; count remains 166,774.
- Existing embeddings untouched; count remains 13. No embeddings generated.
- Original controlled 19 links unchanged; the prior 38 expansion links unchanged; one additional Quran 3:97 link added.
- Existing stations were not updated, deleted, renamed, or merged; `QURAN-01`, WAHY-01, HIJRAH-01, BADR-01, HADITH-01, ST-01 and ST-02 retain their pre-change values.
- No visitors, interactions, app station content, provenance, or source-registry rows were changed.
- Master Content drafts were not inserted.
- Frontend files were not changed; existing `/stations` response shape was preserved.
- No Gemini/external LLM calls, embedding generation, migrations, TTS, image, crowding, RFID, or recommendation work was performed.

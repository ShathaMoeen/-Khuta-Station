# WAHY-01 Reference Resolution Report

**Status: RESOLVED**

## Finding

The four affected WAHY-01 provenance records pointed to the local Arabic Muslim passage `76f07fd73b4ef74f6b74b05d59a32433dc093ac3`, whose stored canonical reference is `muslim:403`. Its text is the Aisha narration about the beginning of revelation: true visions, retreat in Cave Hira, the angel's command to read, and the opening of Surat Al-Alaq. The text clearly supports the WAHY-01 content.

The local dataset also contains a distinct record with reference `muslim:160` (`f83f33a089079492ab937f335b382b2d144cf2cf`). It is a narration about the best form of Islam, feeding people, and greeting people known and unknown. The local records contain no numbering crosswalk establishing that `muslim:403` is equivalent to Sahih Muslim 160. The local `muslim:403` metadata contains no original numbering or crosswalk.

The Al-Dorar takhrij page cited in the earlier content report identifies the beginning-revelation narration and says Muslim recorded it “بنحوه” (similarly): [Al-Dorar narration](https://dorar.net/h/l1gVwvX3). That supports similarity of narration, but does not establish that this local dataset's identifier `muslim:403` maps to the collection number 160. The strict runtime provenance matcher correctly rejects `muslim:403` as equivalent to `Sahih Muslim 160`.

## Affected WAHY-01 records

| Content ID | Variant | Provenance ID | Before | After |
|---:|---|---:|---|---|
| 16 | Arabic intermediate | 616 | Sahih Muslim 160 | `muslim:403` |
| 17 | Arabic advanced | 623 | Sahih Muslim 160 | `muslim:403` |
| 19 | English intermediate | 636 | Sahih Muslim 160 | `muslim:403` |
| 20 | English advanced | 643 | Sahih Muslim 160 | `muslim:403` |

Only the advanced visitor-facing bodies (content IDs 17 and 20) explicitly named “Sahih Muslim 160”; these now describe the source as the local Muslim dataset record `muslim:403`. Intermediate body text was preserved. No beginner content changed.

## Origin and audit trail

The claim appears in `evaluation/results/CONTROLLED_STATION_CONTENT_REPORT.md`, which mapped “Sahih Muslim 160” to the local `muslim:403` passage and characterized the match as exact. The four provenance rows were already present in the database backups made before the Master Content installation. The earlier `FIVE_STATION_EVIDENCE_AUDIT.md` documented Quran 96:1–5 and Bukhari 3 for WAHY-01 and did not establish the Muslim mapping. The old report has not been edited; this report records the correction and supersedes its unsupported numbering equivalence.

A pre-correction snapshot is preserved at `evaluation/results/WAHY_REFERENCE_RESOLUTION_BACKUP_20261006.json`.

## Changes made

- Updated only the four listed WAHY-01 provenance references to the exact local canonical reference `muslim:403`.
- Updated only the two advanced WAHY-01 body texts that explicitly displayed “Sahih Muslim 160”.
- Did not change passage text, station links, embeddings, other station content, or any unrelated rows.
- Did not call Gemini, generate embeddings, run migrations, or run `load_to_db.py`.

## Verification

- Strict runtime evidence validation passes for all six WAHY-01 variants (beginner, intermediate, advanced in Arabic and English); intermediate/advanced variants include the locally stored Muslim evidence and beginner variants do not.
- The strict provenance matcher rejects `muslim:403` as `Sahih Muslim 160`.
- Targeted stale `Sahih Muslim 160` provenance references remaining: 0; canonical `muslim:403` references among the four targeted rows: 4.
- Unit tests: **13 passed** (`tests/test_station_content_flow.py`, `tests/test_citations.py`, `tests/test_rag_safety.py`).
- Database counts after the scoped update:
  - `public.passages`: 166,774
  - `app.embeddings`: 13
  - `app.stations`: 14
  - `app.station_passages`: 58
  - `app.station_content`: 75
  - `app.station_content_provenance`: 280
- No changes were made to the local passage records or station-passage links.

## Remaining data note

The source passage contains some U+FFFD replacement characters in a repeated phrase. They were observed but not changed as part of this reference-only resolution.

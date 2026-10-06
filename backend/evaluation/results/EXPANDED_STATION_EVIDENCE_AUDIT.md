# KHUTA — Expanded Station Evidence Audit

**Audit date:** 2026-10-06  
**Status:** Read-only review. This document does not authorize database use or public display.  
**Scope:** TAWHEED-01, KAABA-01, SALAH-01, SEERAH-01, HISTORY-01, WUDU-01, ZAKAT-01; QURAN-01 and specialized stations are incorporated from `FIVE_STATION_EVIDENCE_AUDIT.md`.

## Method and limits

This audit reviewed existing Quran passage candidates by exact verse reference and topic fit, checked the prior five-station report for already-audited evidence, and inspected the existing station/link inventory. The database remains the source of truth. A stored source label, `sahih`/grade field, or governance label is a database assertion, not independent scholarly verification. We distinguish religious-source standing, database provenance, exact digital text/reference verification, and reuse rights. No independent collation against a printed/authoritative edition, isnad re-evaluation, scholarly review, or rights clearance was performed.

### Source-wide provenance and rights

| Source family | Religious/source reliability | Database provenance and exact verification | Reuse rights |
|---|---|---|---|
| Quran Arabic, `مصحف حفص` | Primary Quran text. | Passage attribution says `Quranpedia.net, dump version 2026-10-03`; source URL `https://quranpedia.net`; local surah/ayah references align with the stored reference. Exact digital text was not independently collated. Registry publisher is null, verification is `unverified`; retrieved/verified dates are null. | `needs_review`; license, license URL, attribution terms are not recorded. Canonical religious status does not establish digital reuse rights. |
| Quran translations | Translation candidates are useful only as translations, not as the Arabic primary text. Existing English label includes Sahih International; French Muhammad Hamidullah; Indonesian Ministry of Religious Affairs; Turkish King Fahd Complex; Urdu label is generic. | Existing matching translation rows were reported in the prior audit; translator/text/reference alignment has not been independently verified here. Registry status is unverified. | License and license URL are absent; rights need review for each translation and edition. |
| Hadith, `quranlab/hadith` | Canonical collection attribution can support candidate relevance; stored grades do not independently establish this export’s exact wording, numbering, chain, or grade. | Dataset URL `https://huggingface.co/datasets/quranlab/hadith`; publisher, version, retrieval date, and export-level verification evidence are absent. Bukhari rows may store `sahih`, `من الصحيحين`, `sahihayn=true`; these are dataset claims. | License/URL and reuse terms missing; rights need review. |
| Tafsir | A named work may be an important source, but a work title alone does not authenticate an excerpt or interpretation. | Earlier audit found 133 Arabic Tafsir rows across its checked references; source registry is unverified. No exact-reference Asbab al-Nuzul rows were found in that scope. Tafsir is not required for the narrow drafts below. | Rights need review; licenses absent. |

The available Quran evidence is Arabic. Do not make visitor-response language a filter that excludes this evidence: a later, approved system may translate/adapt a bounded Arabic master narrative, with citations retained and the translation separately reviewed. Do not treat a generated translation as an authoritative stored translation.

## Candidate evidence for requested stations

All Quran rows listed below are Arabic `quran` records from `مصحف حفص`, locally attributed to the Quranpedia 2026-10-03 dump. Authenticity/grade are not applicable. Provenance, collation and rights caveats are in the table above. IDs are database passage IDs; references are the stored Quran references. The short summaries below are scope notes, not substitute quotations.

### TAWHEED-01 — محطة التوحيد

| Passage ID | Reference | Directly supported topic |
|---|---|---|
| `04a8e5875c8495fdc6502f4d31d409fc030e2f3d` | Quran 112:1 | Allah is One. |
| `2251d4eb44e905148dc3b90981bf7ff8707d49f9` | Quran 112:2 | Allah is al-Samad. |
| `0cb6641828cb2e8783f3ba529ae6c3dde333261c`; `547014de91a9af026cb4118943c13f2c69c9d0fd` | Quran 112:3–4 | Surah al-Ikhlas continues its description of Allah. |
| `4afd60c7cf301fcf1cbf2bd0558745e3f461ddef` | Quran 2:163 | The one God; worship language in the verse. |
| `4aa2ce614f93de1780dc2f465230e98fce1d3e8a` | Quran 6:102 | Allah as Creator and the verse’s worship direction. |
| `1b7af94d1cf44d02513d925873ebc091e17c8816` | Quran 16:36 | Messenger call to worship Allah and avoid taghut. |
| `5d465ae22360b40c539d2fe3e0d9e13f195c279c` | Quran 21:25 | Messenger message and worship of Allah. |
| `a319d939d12f05315e2e5a77e616ec7d10f7c0f6` | Quran 51:56 | Purpose of creation stated in the verse. |
| `15c955999e9a5ae9291110c1497be59a3b953175` | Quran 65:3 | Reliance on Allah in its verse context. |
| `8f24fd47cba4d61e47e1d1221a8ec5fd5ebbda57` | Quran 14:7 | Gratitude and increase, in verse context. |

**Assessment:** Strong narrow educational coverage for oneness, worship, creation, reliance and gratitude. It does not support a detailed creed taxonomy or a comprehensive account of theology. Tafsir is not required for these simple, verse-bounded points; interpretations beyond the wording need qualified review.

### KAABA-01 — محطة الكعبة

| Passage ID | Reference | Directly supported topic |
|---|---|---|
| `bbe35b28cd92a2cc052e9e5df436f36a6fb31bfe` | Quran 2:125 | House, security/place of return, Maqam Ibrahim, and purification in the verse. |
| `dd0a7a5f953b980556c78bf66977eb2f9cfc4cd9` | Quran 2:127 | Ibrahim and Ismail raising the foundations of the House. |
| `e254f72217ac0269fb3843691dfbc8451a0c8ff0` | Quran 2:144 | Direction toward al-Masjid al-Haram. |
| `72f41d9ecaab12efc8683418a64f795648f86d1e` | Quran 3:96 | First House for people at Bakkah, blessed and guidance. |
| `22c982ca1b1d478ec600bd3f3ad310a70d4afbd` | Quran 3:97 | Signs/Maqam Ibrahim and pilgrimage obligation for those able; do not expand into legal advice. |
| `521d22902e94e311146c208f438a7bdf1f58c9f5` | Quran 22:26 | Place of the House and worship-related commands stated there. |
| `4dcbddcec85857a6724a250e21069d4b6d41d04b`; `d8a548dddf770957a6feff7825ea1ddf0232cc9d`; `54bd69793316e4b397fc07a84c10b59a9ac985fd` | Quran 22:27–29 | Pilgrimage proclamation, provision/benefit, vows and circumambulation as stated in the verses. |
| `8ff07ed91297a48d83ca85697eb262e22d121056` | Quran 14:37 | Ibrahim’s prayer concerning descendants settled near the Sacred House. |

**Assessment:** Strong educational coverage for the House, foundations, Qiblah and Hajj connection. No reviewed evidence here for building dates, dimensions, renovations, architectural phases, or Black Stone history.

### SALAH-01 — محطة الصلاة

| Passage ID | Reference | Directly supported topic |
|---|---|---|
| `b724367b4e4cb25d8fae0d30e31c15976441502f` | Quran 2:43 | Prayer and zakat command. |
| `7b097c45df113a0f77a3b0a09bdcd2d721f1e7be` | Quran 20:14 | Worship Allah and establish prayer for remembrance. |
| `3d4409c4a67378b955e6d3cf31f224802a0a6320` | Quran 4:103 | Prayer prescribed at set times; remembrance. |
| `1ddd1aba66388e06518dd530f2be9e65be4b2664` | Quran 11:114 | Prayer at the times stated in the verse and remembrance. |
| `06a1100c7b1b0decc75055a794e68c17504948c9` | Quran 17:78 | Prayer/Quran timing named in the verse. |
| `7f8cd737b04f4b85415f32ae379b4b292226704b` | Quran 29:45 | Recitation, prayer and its stated moral effect. |
| `6d81eeb67a7e222f5bec6a792fb1226c6a2dcc53` | Quran 2:110 | Prayer and zakat command. |

**Assessment:** Sufficient for an educational introduction to prayer’s importance, worship and remembrance. The checked evidence does not justify detailed ritual instructions, legal-school comparisons, or personalized rulings. No new Hadith was required for this bounded draft; the prior HADITH station audit remains separate.

### SEERAH-01 — محطة السيرة

This is a proposed journey hub, not a new evidence set or complete biography. Reuse the prior report’s audited material: WAHY-01 has Quran 96:1–5 and Bukhari 3; HIJRAH-01 has Quran 9:40 and linked Bukhari 5807, with relevant unlinked Bukhari 3905 (`62ab8c44843d8d2ec9e19043ee504d0abc94d94e`); BADR-01 has Quran 3:123–127. Prior audit details, provenance limitations and references remain authoritative for this review. It supports only the three specialized experiences and their evidence-bounded transitions, not a comprehensive Seerah timeline.

### HISTORY-01 — محطة التاريخ

The corpus checks surfaced Quranic event passages but did not establish a reviewed, comprehensive historical source or chronology. Candidates include Quran 33:9 (`435ba0f0aeffca6f37adca2e7811f028c5ae5e29`) and 33:22 (`9add97cc5205c0a0daeb3014e1dc7177c5291820`), which narrate aspects of the Confederates; and Quran 48:18 (`bc2a89a87fec2e5dec837fff9d8859c931ddbd9d`), concerning the pledge under the tree. Treat these as Quranic event vignettes, not a complete or independently dated history. Event identification, chronology and contextual framing need scholarly review before display. **Broad Islamic history is insufficiently supported** by this audit; narrow evidence-bounded vignettes could be educational-only after review.

### WUDU-01 — محطة الوضوء

| Passage ID | Reference | Directly supported topic |
|---|---|---|
| `93737e175c4ed093d8fd976e0dea854594cfcd7a` | Quran 5:6 | Ablution actions and alternatives/conditions named in the verse. |
| `36bd95bdd6a0e31763bd46642ad5ae8ddc241f15` | Quran 4:43 | Purification, major impurity and tayammum context in the verse. |

**Assessment:** Sufficient for a short educational description of what Quran 5:6 explicitly says. The verse should not be expanded into a complete practical/legal guide; conditions, nullifiers, order disputes and individual cases require qualified review.

### ZAKAT-01 — محطة الزكاة

| Passage ID | Reference | Directly supported topic |
|---|---|---|
| `b724367b4e4cb25d8fae0d30e31c15976441502f`; `6d81eeb67a7e222f5bec6a792fb1226c6a2dcc53` | Quran 2:43; 2:110 | Prayer and zakat are commanded together. |
| `3fb9bdf2b40ab47576479b04ee51452ac5285200` | Quran 9:60 | Recipient categories named in the verse. |
| `c2b316a000a2e40a2e1441cb525a6437a1e94936` | Quran 9:103 | Charity from wealth and purification language in the verse context. |
| `5cc1aaeb272a9e5d59e23c3e4687a1ed78afb2be` | Quran 9:71 | Believers’ mutual support, prayer, zakat and obedience as stated. |
| `15957d18591c89eeaa540caf32525c81995c8411` | Quran 2:177 | Righteousness includes giving to named recipients and zakat, among other matters. |

**Assessment:** Sufficient for educational coverage of importance and the explicitly named recipient categories. It does not support personal eligibility determinations, nisab, rates, asset treatment, due dates, or individual calculation in this audit.

## Existing stations and read-only inventory

The live station inventory returned BADR-01 (5 links), HADITH-01 (1), HIJRAH-01 (2), QURAN-01 (5), WAHY-01 (6), plus unlinked ST-01 and ST-02. The seven requested new codes TAWHEED-01, KAABA-01, SALAH-01, SEERAH-01, HISTORY-01, WUDU-01 and ZAKAT-01 were not present. No station or relationship was created. HADITH-01 remains separate; its single current Bukhari 3 link is topic-misaligned for a general Hadith introduction per the prior audit.

| Station | Evidence Quality | Coverage | Recommended Scope | Ready for Master Content? |
|---|---|---|---|---|
| TAWHEED-01 | Strong primary Quran candidates; digital source rights/collation unverified | Oneness, worship, Creator, reliance, gratitude | Short verse-bounded educational introduction; no creed taxonomy | Yes — draft only, review required |
| KAABA-01 | Strong primary Quran candidates; rights/collation unverified | House, foundations, Qiblah, pilgrimage | Scriptural significance only; no architecture/history claims | Yes — draft only, review required |
| SALAH-01 | Strong primary Quran candidates; rights/collation unverified | Importance, worship, remembrance, timing references | Educational significance, not a ritual/fiqh manual | Yes — draft only, review required |
| SEERAH-01 | Existing audited Quran/Hadith evidence; Hadith export and rights unverified | Revelation, Hijrah, Badr only | Overview/hub linking specialized experiences | Partial — bounded hub draft only |
| HISTORY-01 | Quranic event candidates; broad historical source/chronology not established | A few event vignettes, not a timeline | Narrow, reviewed Quranic event vignettes or defer | No for broad station; conditional educational-only draft |
| QURAN-01 | Prior audit: primary Quran rows; digital provenance/rights unverified | Introductory verses on guidance, reflection, reading | Use prior report’s limited scope | Yes — use prior draft/evidence map |
| WUDU-01 | Primary Quran evidence; rights/collation unverified | Explicit actions/conditions in 5:6 | Verse description only; no individualized/legal guide | Yes — draft only, review required |
| ZAKAT-01 | Primary Quran evidence; rights/collation unverified | Importance and named categories | Educational overview, no personal calculation/rulings | Yes — draft only, review required |

## Governance and implementation boundary

- General Ask: educational answers bounded to approved, human-reviewed master content and retrieved evidence. Preserve citations and abstain when evidence is missing.
- Personal fatwa or individualized worship/financial ruling: do not answer as a ruling; refer to qualified human guidance.
- Do not infer religion, sect, politics, or other sensitive traits from visitor behavior.
- Proposed journey only: SEERAH-01 as overview/hub → specialized WAHY-01, HIJRAH-01 and BADR-01 experiences. HADITH-01 remains separate. This is a recommendation, not a database relationship change.
- Later station recommendation should consider visitor-stated interests, visitor level, visited/unvisited stations, journey relevance and current crowd estimate. HIGH-crowding stations should be deprioritized when a suitable lower-crowding choice exists. No recommendation engine change was made.
- Each station may eventually show one approved image on first open. Require item-level provenance, creator/provider, license/reuse status and attribution. No image was acquired. No image during Ask.
- TTS is suitable only after text approval and must narrate exactly the final approved visitor-facing text; it must not embellish.

## Read-only final verification

| Check | Observed value |
|---|---:|
| `public.passages` | 166,774 |
| `app.embeddings` | 13 |
| `app.station_passages` | 19 |

Station inventory remained the five active controlled stations plus ST-01/ST-02; none of the seven proposed new station codes existed. This task performed SELECT-only database checks and created review documents only. No rows or links were changed; no station was created/deleted; no embeddings were generated; no frontend files were changed; no Gemini/external LLM was called; no migration or ingestion was run. The prior `FIVE_STATION_EVIDENCE_AUDIT.md` was not modified.

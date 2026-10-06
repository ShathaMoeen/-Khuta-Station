# KHUTA — Five-Station Trusted-Evidence Audit

**Audit date:** 2026-10-06  
**Mode:** Read-only database and repository inspection. No Gemini calls. No inserts, updates, deletes, migrations, embedding changes, passage changes, or station-link changes were performed.

## Scope and method

Audited only `QURAN-01`, `WAHY-01`, `HIJRAH-01`, `BADR-01`, and `HADITH-01`; excluded `ST-01` and `ST-02`. The database was treated as the source of truth. Inspection used read-only `SELECT` queries against `public.passages`, `app.stations`, `app.station_passages`, and `app.content_sources`. Discovery used exact verse references, current station links, Arabic Hadith keyword searches, and direct review of candidate text/metadata. A keyword match alone was not accepted as evidence. Badr search yielded many incidental mentions; only event-relevant, reviewed candidates are recommended below.

The audit distinguishes (1) scholarly/religious reliability, (2) database provenance, (3) exact-reference verification, and (4) reuse rights. Local `APPROVED_LEVEL_2` is a governance field; it does not resolve provenance, license, publisher, or independent-verification gaps.

## Source and language findings

| Source family | Database facts | Reliability/provenance interpretation | Reuse rights |
|---|---|---|---|
| Quran Arabic (`مصحف حفص`) | Passage attribution `Quranpedia.net, dump version 2026-10-03`; URL `https://quranpedia.net`. Source registry version `2026-10-03`; publisher null; registry verification `unverified`; retrieved/verified timestamps null. | The Quran is primary religious text. Local verse references align internally with stored `surah`/`ayah`; no independent Mushaf collation was performed. | `rights_status=needs_review`; license/license URL null. Canonical religious status does not establish digital reuse rights. |
| Quran translations | Matching verses exist in English, French, Indonesian, Turkish, and Urdu. Labels include Sahih International (English), Muhammad Hamidullah (French), Indonesian Ministry of Religious Affairs, King Fahd Complex (Turkish), and generic Urdu label. | Availability only; translation text/translator attribution has not been independently checked. Registry sources unverified. | Registry license/license URL null and rights `needs_review`. |
| Hadith (`quranlab/hadith`) | Arabic subsets for Bukhari, Muslim, Abu Dawud, Tirmidhi, Ibn Majah, Nasa'i, Malik. Source URL `https://huggingface.co/datasets/quranlab/hadith`. Publisher, version, retrieval date, passage attribution, license/license URL, verification evidence are absent; registry `unverified`. | Bukhari candidate rows say `authenticity=sahih`, `grade=من الصحيحين`, `sahihayn=true`, `authenticity_basis=الصحيحان`. Abu Dawud candidates include named grade strings. These are dataset claims supporting candidate selection, not independent verification of this export’s exact text, isnad, numbering, or grading. | Hadith source records are `needs_review`; no license/license URL. |
| Tafsir / Asbab al-Nuzul | At the audited references (96:1–5, 9:40, 3:123–127 and selected intro verses), 133 Arabic Tafsir rows were found; exact-reference Asbab rows: 0. Named Tafsir sources include `تفسير ابن أبي حاتم`, `تفسير القرآن العظيم`, `جامع البيان`, and `المختصر في تفسير القرآن الكريم`; Quranpedia dump attribution is generally `2026-08-10`. | A work title does not independently authenticate a particular excerpt. Registry records are unverified. Not needed for the compact evidence sets below. | Rights are `needs_review`; licenses blank. |

### Current station links (read-only)

| Station | Links | Finding |
|---|---:|---|
| QURAN-01 | 5 | Quran 96:1–5 only. Useful reading/learning evidence, but not a general introduction by itself. |
| WAHY-01 | 6 | Quran 96:1–5 plus Bukhari 3; aligned to beginning of revelation. |
| HIJRAH-01 | 2 | Quran 9:40 plus Bukhari 5807. Other relevant Hadith exists unlinked. |
| BADR-01 | 5 | Quran 3:123–127. Relevant Bukhari reports are present but not linked. |
| HADITH-01 | 1 | Bukhari 3, about beginning of revelation; not a Hadith/Sunnah introduction. Topic-alignment gap. |

## 1. QURAN-01 — القرآن الكريم

**Purpose:** An evidence-bounded introduction to the Quran as a revealed book, guidance, reading/learning, and reflection.

### Recommended evidence

All Quran rows below: type `quran`, language `ar`, source `مصحف حفص`, attribution `Quranpedia.net, dump version 2026-10-03`, URL `https://quranpedia.net`; authenticity/grade N/A. Relevance confidence is per row. Source reliability is primary Quran text, but this digital text/reference was not independently collated. Registry publisher null, `verification_status=unverified`, `rights_status=needs_review`, license/license URL null. The local reference matches the row’s `surah`/`ayah` fields. Matching translations in English/French/Indonesian/Turkish/Urdu exist but have their own unverified provenance and rights review.

| passage_id | Reference | Excerpt/summary and station fit | Relevance confidence |
|---|---|---|---|
| `1b57193e45df20b425be106d7d3fa24d92545808` | 2:2 | Describes the Book as guidance for the mindful. | High |
| `dd9576d4cd6ca7b97306ef32228f3c5334c4b3c8` | 17:9 | Says the Quran guides to what is most upright and gives glad tidings. | High |
| `64c03127a5d6d696c338b71b6c0435690b66707c` | 38:29 | A blessed Book sent down so its verses may be reflected upon. | High |
| `4501640cbf4bf52e349fb9ea12c1bb2fec492289` | 96:1 | Command to read in the name of the Creator; also relevant to WAHY-01. | High |
| `be78d863615f938338f255ea51c27c9ca349686c` | 96:2 | Human creation; part of the opening passage, less central to this station purpose. | Medium |
| `37abf956c3134f77007b4e491765708e9a34b09e` | 96:3 | Repeats the command to read. | High |
| `432cc9475e5938c28ef2fa778f77c6bd117c2100` | 96:4 | Teaching by the pen. | High |
| `18600315950025708ffe7bdb7543dac606a886b6` | 96:5 | Teaching the human what they did not know. | High |

### Proposed Master Content structure

1. Guidance — 2:2 and 17:9.
2. Revelation and reflection — 38:29.
3. Reading, teaching, learning — 96:1–5.
4. **Unsupported:** full compilation/transmission history or broad theological definitions; these verses do not establish those topics.

**Content coverage:** `EDUCATIONAL_ONLY`  
**Missing evidence:** Reviewed educational source if compilation history, definition, or additional theology is desired.  
**Image concept:** Museum-safe Quran manuscript detail or abstract calligraphic exhibit visual; later verify object/image provenance, reproduction rights, license, attribution, and sacred-text display restrictions.  
**Audio suitability:** Yes, after review; TTS must narrate the exact reviewed visitor text only, with references available to the visitor.

## 2. WAHY-01 — بداية الوحي

**Purpose:** Explain the beginning of revelation without adding narrative details from model memory.

### Recommended evidence

Quran 96:1–5 are the five records above. Additional candidate:

| passage_id | Type / language | Source / reference | Authenticity / grade / attribution | Summary, station fit, confidence | Scholarly reliability / provenance / rights |
|---|---|---|---|---|---|
| `bb9bec5713b6f005ee24fefeaf49ad4c95cc9a77` | hadith / ar | `quranlab/hadith:bukhari-ar` / `bukhari:3` | `sahih`; `من الصحيحين`; attribution null | Aisha’s report covers true dreams before Hira, retreat at Hira, the command to read, return to Khadija, her response, Waraqa, and the pause in revelation. **Very high** relevance. | Strong canonical collection at work level; local text/ref/numbering are dataset assertions not independently collated. URL HF `quranlab/hadith`; registry version, publisher, retrieval date, license missing; registry unverified/rights needs review. |

Quran source metadata and trust caveats are as described in QURAN-01. Bukhari row also stores `sahihayn=true`, `authenticity_basis=الصحيحان`.

### Proposed Master Content structure

1. Reported prelude: true dreams (Bukhari 3; attribute to Aisha’s report).
2. Hira and first command: Bukhari 3 with Quran 96:1–5.
3. Return/support: Khadija’s response as reported in Bukhari 3.
4. Waraqa and pause: Bukhari 3; distinguish Hadith report from Quran text.
5. **Unsupported:** exact date, added staging/dialogue, and full later revelation chronology.

**Content coverage:** `PARTIAL` (coherent beginning-of-revelation account, not complete revelation history).  
**Missing evidence:** Independent Bukhari text/ref and edition-number review; rights review; additional context if desired.  
**Image concept:** Hira/Jabal al-Nour landscape without depicting the Prophet ﷺ or angelic figures; verify site/image provenance, creator rights, license, attribution, location restrictions.  
**Audio suitability:** Yes after source/translation review; no invented dialogue or dramatic detail.

## 3. HIJRAH-01 — الهجرة إلى المدينة

**Purpose:** Present the migration journey only as locally evidenced, distinguishing Quran from Hadith.

### Recommended evidence

Quran 9:40 is Arabic `مصحف حفص`, N/A authenticity/grade, Quranpedia attribution/version 2026-10-03, URL `https://quranpedia.net`; source registry unverified and rights needs review. It describes the two in the cave, reassurance, and divine support.

| passage_id | Type / language | Source / reference | Authenticity / grade / attribution | Summary, station fit, confidence | Scholarly reliability / provenance / rights |
|---|---|---|---|---|---|
| `b1fc3f4c375823406cd257241fed68300c9e4af3` | quran / ar | مصحف حفص / 9:40 | N/A / N/A / Quranpedia dump 2026-10-03 | Cave, companion, reassurance and divine support. **Very high** relevance. | Primary Quran text; locally aligned reference, not independently collated. Registry unverified, rights needs review, license blank. |
| `62ab8c44843d8d2ec9e19043ee504d0abc94d94e` | hadith / ar | quranlab/hadith:bukhari-ar / bukhari:3905 | `sahih` / `من الصحيحين`; attribution null | Long Aisha report covers preparation with Abu Bakr, three nights at Thawr, support arrangements, guide/route, pursuit, and arrival in Medina. **Very high**, strongest locally found journey narrative. | Strong at collection level; exact exported text/ref unverified. HF URL; version/publisher/retrieval date/license absent; registry unverified, rights needs review. |
| `da465102c3a98b3817b6cadce070e2a1a7b530bb` | hadith / ar | quranlab/hadith:bukhari-ar / bukhari:3911 | `sahih` / `من الصحيحين`; attribution null | Arrival in Medina, reception by Ansar, and stay at Abu Ayyub’s home. **High**, complementary arrival account. | Same Bukhari provenance and rights caveat above. |
| `c94fa68dbed289d05f61130799a321b97a30f495` | hadith / ar | quranlab/hadith:bukhari-ar / bukhari:3653 | `sahih` / `من الصحيحين`; attribution null | Abu Bakr’s report of the cave moment and reassurance as pursuers were nearby. **High**; pairs with Quran 9:40. | Same Bukhari provenance and rights caveat above. |

### Proposed Master Content structure

1. Preparation and companionship — Bukhari 3905.
2. Cave and companion — Quran 9:40 plus Bukhari 3905/3653; keep source types distinct.
3. Support and route — Bukhari 3905 only; no added landmarks.
4. Arrival — Bukhari 3905 and 3911.
5. **Unsupported:** additional dates, route landmarks, motives, dialogue, or later events not in selected text.

**Content coverage:** `PARTIAL` (substantial journey account exists, but remains a scoped narration subject to source review).  
**Missing evidence:** Independent text/ref/numbering review, source rights, translation review, and evidence for any additional route details.  
**Image concept:** Historically cautious Makkah–Medina route map or non-figurative Thawr landscape; verify route basis, map-data/image license, creator, attribution, protected-site restrictions.  
**Audio suitability:** Yes after review; Quran/Hadith distinctions and citations retained, no added scenery/dialogue.

## 4. BADR-01 — غزوة بدر

**Purpose:** Expand audit coverage beyond the existing Quran 3:123–127 links. No new station links are proposed/applied here.

The five Quran passages are Arabic `مصحف حفص`, Quranpedia attribution/version 2026-10-03, Quran source caveats as above. The Hadith candidates are Arabic Bukhari rows from `quranlab/hadith:bukhari-ar`, URL `https://huggingface.co/datasets/quranlab/hadith`; each locally says `sahih`, `من الصحيحين`, `sahihayn=true`, `authenticity_basis=الصحيحان`; passage attribution null; source registry unverified, with version/publisher/retrieval date/license missing and rights `needs_review`.

| passage_id | Type / language | Source / reference | Authenticity / grade / attribution | Summary, station fit, confidence | Scholarly reliability / provenance / rights |
|---|---|---|---|---|---|
| `74a24002de6cb4e43a98b054fab0130e1543019f` | quran / ar | مصحف حفص / 3:123 | N/A / N/A / Quranpedia 2026-10-03 | Explicitly names Badr; victory despite weakness/few numbers; gratitude. **Very high**. | Quran source status above. |
| `4b6c9e9868c98250b8b1a5fa3d520d77613b5249` | quran / ar | مصحف حفص / 3:124 | N/A / N/A / Quranpedia 2026-10-03 | Promise of three thousand angels. **Very high**. | Quran source status above. |
| `8b59347ff11f8dedc10cdfe3f1cce8e7caf2635f` | quran / ar | مصحف حفص / 3:125 | N/A / N/A / Quranpedia 2026-10-03 | Conditional promise of five thousand marked angels. Preserve its conditions. **Very high**. | Quran source status above. |
| `088141735e5473ae8668268c4286cb1b8b726d65` | quran / ar | مصحف حفص / 3:126 | N/A / N/A / Quranpedia 2026-10-03 | Reassurance/good news and victory from God. **Very high**. | Quran source status above. |
| `b5a6e23fdd0972f4a538f875d6b4727b56e9ac1e` | quran / ar | مصحف حفص / 3:127 | N/A / N/A / Quranpedia 2026-10-03 | States outcome as cutting off a portion or subduing them; do not expand to all opponents. **Very high**. | Quran source status above. |
| `11118a767afb2860c483b2868aa7fe9fca511b4a` | hadith / ar | quranlab/hadith:bukhari-ar / bukhari:3951 | `sahih` / `من الصحيحين`; attribution null | Intended caravan and unexpected meeting with the enemy. **Very high** context relevance. | Bukhari work-level reliability strong; local export/ref unverified. Rights needs review. |
| `b4593d83a93f40ef4ead6b70467f7fdb97f5cd54` | hadith / ar | quranlab/hadith:bukhari-ar / bukhari:3953 | `sahih` / `من الصحيحين`; attribution null | Ibn Abbas report of supplication on Badr, Abu Bakr’s response, and Quranic words. **High** relevance. | Same Bukhari provenance/rights caveat. |
| `f94b52e6a7a297bd1e4c992a0ad66e18eefa9bbf` | hadith / ar | quranlab/hadith:bukhari-ar / bukhari:3956 | `sahih` / `من الصحيحين`; attribution null | Al-Bara reports approximate emigrant/Ansar counts. Preserve the approximate language, not a precise total. **High**. | Same Bukhari provenance/rights caveat. |
| `796cc5ab94de05cd7395846ba0e6028fdc03081e` | hadith / ar | quranlab/hadith:bukhari-ar / bukhari:3976 | `sahih` / `من الصحيحين`; attribution null | Report about 24 Quraysh leaders at the well and the later address. **Very high** event/outcome relevance; sensitive content requires editorial review. | Same Bukhari provenance/rights caveat. |
| `9731d765d98afebd4d2c4430d618d32efee1606b` | hadith / ar | quranlab/hadith:bukhari-ar / bukhari:3992 | `sahih` / `من الصحيحين`; attribution null | Report about Badr participants and angels who witnessed Badr. **High** bounded-significance relevance. | Same Bukhari provenance/rights caveat. |
| `e03e51a29b27a59d8df20aab96d2825c8c5b9071` | hadith / ar | quranlab/hadith:bukhari-ar / bukhari:3995 | `sahih` / `من الصحيحين`; attribution null | Ibn Abbas report of Gabriel at Badr equipped for battle. **High**; label as Hadith, not Quran. | Same Bukhari provenance/rights caveat. |
| `ca880913cffc0c54ef5ef89a35d41061d21536b2` | hadith / ar | quranlab/hadith:bukhari-ar / bukhari:3998 | `sahih` / `من الصحيحين`; attribution null | Al-Zubayr report of one specific combat encounter. **High** for one episode, not complete chronology. | Same Bukhari provenance/rights caveat. |

Matching Quran translations in English/French/Indonesian/Turkish/Urdu exist. These Hadith candidates are Arabic only; output language need not filter out Arabic primary evidence.

### Proposed Master Content structure

1. Context — Bukhari 3951 (caravan intent, unexpected meeting), without broader unsupported causes.
2. Participants — Bukhari 3956 approximate groups/counts; Bukhari 3998 one named participant/encounter.
3. Event detail — Bukhari 3976, with editorial review.
4. Divine support — Quran 3:123–126 plus Bukhari 3992/3995, distinguished by source type.
5. Outcome — Quran 3:127 and bounded Bukhari 3976 narration.
6. Reflection — gratitude/victory-from-God themes in Quran 3:123/126 only. Other lessons are **UNSUPPORTED** by this set.

**Content coverage:** `PARTIAL`  
**Missing evidence:** Full chronology, detailed battle movements, comprehensive military context, full participant roster, broader aftermath. Tafsir exists at audited references, but candidate works are unverified/rights-needing-review and are not an approved substitute. Bukhari text/reference/edition numbering needs human collation.  
**Image concept:** Historically cautious Badr landscape or educational map; no staged battle or sacred figures. Verify historical/geographic basis, map/image rights, creator, license, attribution.  
**Audio suitability:** Yes for a partial, reviewed account; preserve conditional/partitive Quran wording and label Quran/Hadith sources.

## 5. HADITH-01 — السنة والحديث

**Purpose:** Bounded education about transmission, accurate attribution, and Sunnah. The local corpus does not provide a comprehensive definition/methodology source.

All records below are Arabic from `quranlab/hadith`, URL `https://huggingface.co/datasets/quranlab/hadith`; passage attribution null. Registry publisher/version/retrieval date/license/license URL are absent, verification is unverified, rights are `needs_review`.

| passage_id | Type / language | Source / reference | Authenticity / grade / attribution | Summary, station fit, confidence | Scholarly reliability / provenance / rights |
|---|---|---|---|---|---|
| `b1b24fae69ed7aac008861246faf7d985062a9f0` | hadith / ar | quranlab/hadith:bukhari-ar / bukhari:3461 | `sahih` / `من الصحيحين`; attribution null | Conveying what was heard and warning against deliberate false attribution. **Very high** bounded transmission example. | Bukhari collection strong at work level, local copy/ref unverified; rights needs review. |
| `7185faf078a890d69aa254e1296f81398459513b` | hadith / ar | quranlab/hadith:bukhari-ar / bukhari:107 | `sahih` / `من الصحيحين`; attribution null | Narrator’s caution because of the warning against lying about the Prophet. **High**. | Same Bukhari provenance/rights caveat. |
| `0ce1eaa087e33e748907c94fffc4ab3ce2ac9dd9` | hadith / ar | quranlab/hadith:abudawud-ar / abudawud:4607 | `sahih`; local grades: Al-Albani Sahih; Muhammad Muhyi Al-Din Abdul Hamid Sahih; Zubair Ali Zai Isnaad Sahih; attribution null | Instruction to hold to the Sunnah and the rightly guided caliphs’ Sunnah. **High**. | Named grades are local metadata; not independently regraded. Export/ref unverified; rights needs review. |
| `79a81f4403df53c338ff5ef9d35f47888b2cfcd9` | hadith / ar | quranlab/hadith:abudawud-ar / abudawud:3660 | `sahih`; local grades: Al-Albani Sahih; Muhammad Muhyi Al-Din Abdul Hamid Sahih; Zubair Ali Zai Isnaad Sahih; attribution null | Hearing, retaining, and conveying Hadith; recipient may understand more deeply. **High**. | Named grades are local metadata; not independently regraded. Export/ref unverified; rights needs review. |

### Proposed Master Content structure

1. What these reports say about conveying and preserving reports — cite the Hadith examples.
2. Accurate attribution — Bukhari 3461/107; do not claim a complete verification system.
3. Transmission and understanding — Abu Dawud 3660, after review.
4. Sunnah as guidance — Abu Dawud 4607, after review.
5. **Unsupported:** comprehensive definition of Hadith/Sunnah, compilation chronology, narrator-classification rules, authentication methodology, legal-school differences. Obtain a reviewed educational source first.

**Content coverage:** `EDUCATIONAL_ONLY` (bounded transmission/Sunnah explanation; not enough for methodology instruction).  
**Missing evidence:** Publisher-identified, rights-cleared, scholarly-reviewed introductory source defining Hadith/Sunnah and explaining methodology. Current Bukhari 3 link is about revelation and does not fill this gap.  
**Image concept:** Catalogued Hadith manuscript or manuscript-focused educational image; verify repository record, dating, image provider, reproduction license, attribution, display rights.  
**Audio suitability:** Suitable only for the bounded explanation after Hadith/right review; do not turn examples into broad methodology claims.

## Image and audio constraints for later implementation

- One selected, rights-cleared image may appear when a station opens; Ask KHUTA follow-ups must not repeat it.
- Do not use arbitrary search results. Verify provenance, historical/visual accuracy, license, and attribution before use.
- TTS must narrate the exact reviewed visitor-facing text after grounded personalization and citation validation. It must not add or embellish claims. Keep citations available to the visitor even if not spoken.

## Final summary

| Station | Evidence quality | Content coverage | Ready for Master Content? |
|---|---|---|---|
| QURAN-01 | Strong primary Quran verses; digital text/rights not verified | EDUCATIONAL_ONLY | Yes, bounded draft for scholarly review; no public approval yet. |
| WAHY-01 | Quran plus directly relevant Bukhari; provenance/rights unresolved | PARTIAL | Yes, scoped draft; verify text/ref and rights. |
| HIJRAH-01 | Quran 9:40 plus detailed Bukhari journey/arrival reports | PARTIAL | Yes, scoped draft; verify text/ref and rights. |
| BADR-01 | Quran set plus several event-relevant Bukhari candidates | PARTIAL | Yes, partial story draft only; review sensitive details, references, rights. |
| HADITH-01 | Useful graded examples; current link is misaligned | EDUCATIONAL_ONLY | Conditional: bounded transmission/Sunnah draft; stronger introductory source needed for methodology. |

## RECOMMENDED NEXT STEP

Proceed to human-reviewed, evidence-mapped drafts for QURAN-01, WAHY-01, HIJRAH-01, and a deliberately partial BADR-01 story. HADITH-01 should remain bounded to transmission, attribution care, and Sunnah until a scholarly-reviewed introductory source is identified. Before approving public content, collate exact Quran/Hadith text and references, review translation/religious framing, identify the Hadith dataset publisher/version, and resolve license/attribution rights. Existing governance labels do not substitute for these checks.

**No Master Stories were generated or saved. No database data, station links, provenance, embeddings, governance, frontend, or `public.passages` were modified. No live Gemini generation was used.**

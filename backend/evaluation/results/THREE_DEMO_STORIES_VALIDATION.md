# Three Approved Arabic Demo Stories — Validation

Date: 2026-10-06

## Scope and backup

Installed only the approved Arabic/intermediate stories for WAHY-01, HIJRAH-01, and BADR-01. Existing row IDs were retained. No frontend, Ask KHUTA, RFID, crowding, recommendation, migration, or ingestion code was changed. No Gemini request was made.

Pre-edit backup: [THREE_DEMO_STORIES_PRE_EDIT_BACKUP_20261006.json](C:/Users/shada/Downloads/islamic-ai-challenge/backend/evaluation/results/THREE_DEMO_STORIES_PRE_EDIT_BACKUP_20261006.json)

The reversible snapshot contains all 18 `app.station_content` rows for the three stations, their 74 `app.station_content_provenance` rows, and all 13 `app.station_passages` rows for those stations. It records the pre-edit counts as well.

## Installed rows

| Station | Station ID | `station_content` row ID | Exact language/level | Result |
|---|---:|---:|---|---|
| WAHY-01 | 10 | 16 | ar / intermediate | Updated in place |
| HIJRAH-01 | 11 | 22 | ar / intermediate | Updated in place |
| BADR-01 | 12 | 28 | ar / intermediate | Updated in place |

No beginner, advanced, or English content variant was updated. All three titles and bodies were written exactly as supplied. The HTTP response body equaled the selected database body for each route.

## WAHY-01 — evidence and API output

Station ID: `10`; content row ID: `16`.

Bukhari 3 supports seclusion at Hira, the command “اقرأ”, the initial verses, the return to Khadijah, and her reassurance. Local Quran 96:1–5 supports the cited verse span. Existing `muslim:403` provenance was preserved; it was not rewritten to another numbering scheme.

| Local source | Provenance reference | Local passage reference | Passage ID | Source verification / rights |
|---|---|---|---|---|
| quranlab/hadith:bukhari-ar | Sahih al-Bukhari 3 | bukhari:3 | `bb9bec5713b6f005ee24fefeaf49ad4c95cc9a77` | unverified / needs_review |
| quranlab/hadith:muslim-ar | muslim:403 | muslim:403 | `76f07fd73b4ef74f6b74b05d59a32433dc093ac3` | unverified / needs_review |
| مصحف حفص | Quran 96:1 | 96:1 | `4501640cbf4bf52e349fb9ea12c1bb2fec492289` | unverified / needs_review |
| مصحف حفص | Quran 96:2 | 96:2 | `be78d863615f938338f255ea51c27c9ca349686c` | unverified / needs_review |
| مصحف حفص | Quran 96:3 | 96:3 | `37abf956c3134f77007b4e491765708e9a34b09e` | unverified / needs_review |
| مصحف حفص | Quran 96:4 | 96:4 | `432cc9475e5938c28ef2fa778f77c6bd117c2100` | unverified / needs_review |
| مصحف حفص | Quran 96:5 | 96:5 | `18600315950025708ffe7bdb7543dac606a886b6` | unverified / needs_review |

API citations returned (7): `muslim:403`, `96:1`, `96:2`, `96:3`, `96:4`, `96:5`, `bukhari:3`.

API checks: HTTP 200; visitor language `ar`, level `intermediate`; exact title; nonempty readable sources; `personalized_explanation == content.body`; `explanation_source=database`; `ai_generated=false`; `ai_status=database_content`. No passage IDs, source IDs, vector scores, or ranking fields appeared in the visitor citations.

Exact API `content.body`:

```text
في غار حراء تبدأ هذه المحطة من لحظة عظيمة في السيرة النبوية.

كان رسول الله ﷺ يحب الخلوة، فيذهب إلى غار حراء ويتعبد فيه لياليَ متعددة. وفي إحدى تلك الخلوات جاءه المَلَك وقال له: «اقرأ». فأجابه النبي ﷺ: «ما أنا بقارئ». وتكرر الأمر، ثم تلا عليه المَلَك أول ما نزل من سورة العلق: ﴿اقْرَأْ بِاسْمِ رَبِّكَ الَّذِي خَلَقَ﴾ حتى قوله تعالى: ﴿عَلَّمَ الْإِنسَانَ مَا لَمْ يَعْلَمْ﴾.

عاد رسول الله ﷺ إلى خديجة رضي الله عنها وقد أصابه الخوف من هول ما شهد، وقال: «زملوني زملوني». فطمأنته خديجة رضي الله عنها وذكّرته بما عُرف عنه من صلة الرحم وصدق الحديث وإكرام الضيف وإعانة الناس.

من هنا تبدأ رحلة الوحي؛ بكلمة «اقرأ»، لتفتح مرحلة جديدة من رسالة النبي محمد ﷺ.
```

## HIJRAH-01 — evidence and API output

Station ID: `11`; content row ID: `22`.

Quran 9:40 supports the cave and “لا تحزن إن الله معنا”. Bukhari 3653 contains Abu Bakr’s statement about looking beneath the feet and the Prophet’s “ما ظنك يا أبا بكر باثنين الله ثالثهما؟” response. Bukhari 3922 supports Abu Bakr seeing the pursuers’ feet. Existing Bukhari 5807 provenance was retained.

| Local source | Provenance reference | Local passage reference | Passage ID | Source verification / rights |
|---|---|---|---|---|
| quranlab/hadith:bukhari-ar | Sahih al-Bukhari 3653 | bukhari:3653 | `c94fa68dbed289d05f61130799a321b97a30f495` | unverified / needs_review |
| quranlab/hadith:bukhari-ar | Sahih al-Bukhari 3922 | bukhari:3922 | `468f5613230814f1f0e7e5b443dd19dcb88efd85` | unverified / needs_review |
| quranlab/hadith:bukhari-ar | Sahih al-Bukhari 5807 | bukhari:5807 | `2d5eb2f7011c3908572dc9e99eeab9ac0231da99` | unverified / needs_review |
| مصحف حفص | Quran 9:40 | 9:40 | `b1fc3f4c375823406cd257241fed68300c9e4af3` | unverified / needs_review |

API citations returned (4): `9:40`, `bukhari:3653`, `bukhari:3922`, `bukhari:5807`.

API checks: HTTP 200; visitor language `ar`, level `intermediate`; exact title; nonempty readable sources; `personalized_explanation == content.body`; `explanation_source=database`; `ai_generated=false`; `ai_status=database_content`. No passage IDs, source IDs, vector scores, or ranking fields appeared in the visitor citations.

Exact API `content.body`:

```text
تأخذك هذه المحطة إلى واحدة من أبرز لحظات الهجرة النبوية.

خرج رسول الله ﷺ ومعه أبو بكر الصديق رضي الله عنه، وفي أثناء الهجرة كانا في الغار، بينما اقترب منهما من يبحث عنهما حتى رأى أبو بكر أقدامهم.

قال أبو بكر رضي الله عنه للنبي ﷺ إن أحدهم لو نظر تحت قدميه لرآهما. لكن النبي ﷺ أجابه بكلمات مليئة بالثقة بالله: «ما ظنك يا أبا بكر باثنين الله ثالثهما؟».

وقد خلد القرآن هذه اللحظة في قوله تعالى: ﴿لَا تَحْزَنْ إِنَّ اللَّهَ مَعَنَا﴾.

لم تكن هذه اللحظة مجرد اختباء في غار؛ بل كانت موقفًا يظهر فيه التوكل على الله والثقة بنصره في وقت شديد الخطر.

ومن الغار تستمر رحلة الهجرة، حاملةً معها معنى بقي حاضرًا عبر القرون: ﴿إِنَّ اللَّهَ مَعَنَا﴾.
```

## BADR-01 — evidence and API output

Station ID: `12`; content row ID: `28`.

Sahih Muslim `muslim:4588` locally supports the 319/1,000 figures, facing the qiblah, raising hands and supplicating, the cloak falling, and Abu Bakr replacing it. Quran 8:9 supports the quoted supplication/response, 3:123 mentions Badr, and 3:126 supports the final victory wording. Existing links to Quran 3:124, 3:125, and 3:127 were preserved.

| Local source | Provenance reference | Local passage reference | Passage ID | Source verification / rights |
|---|---|---|---|---|
| quranlab/hadith:muslim-ar | muslim:4588 | muslim:4588 | `3c86805857572b26ec877bf011d83b7476e30c18` | unverified / needs_review |
| مصحف حفص | Quran 3:123 | 3:123 | `74a24002de6cb4e43a98b054fab0130e1543019f` | unverified / needs_review |
| مصحف حفص | Quran 3:124 | 3:124 | `4b6c9e9868c98250b8b1a5fa3d520d77613b5249` | unverified / needs_review |
| مصحف حفص | Quran 3:125 | 3:125 | `8b59347ff11f8dedc10cdfe3f1cce8e7caf2635f` | unverified / needs_review |
| مصحف حفص | Quran 3:126 | 3:126 | `088141735e5473ae8668268c4286cb1b8b726d65` | unverified / needs_review |
| مصحف حفص | Quran 3:127 | 3:127 | `b5a6e23fdd0972f4a538f875d6b4727b56e9ac1e` | unverified / needs_review |
| مصحف حفص | Quran 8:9 | 8:9 | `94aa7fd04884d5f7187fee705e5136ecb776fa1e` | unverified / needs_review |

API citations returned (7): `muslim:4588`, `3:123`, `3:124`, `3:125`, `3:126`, `3:127`, `8:9`.

API checks: HTTP 200; visitor language `ar`, level `intermediate`; exact title; nonempty readable sources; `personalized_explanation == content.body`; `explanation_source=database`; `ai_generated=false`; `ai_status=database_content`. No passage IDs, source IDs, vector scores, or ranking fields appeared in the visitor citations.

Exact API `content.body`:

```text
نصل في هذه المحطة إلى يوم بدر.

كان المسلمون يومها ثلاثمائة وتسعة عشر رجلًا، بينما كان المشركون ألفًا. نظر رسول الله ﷺ إلى هذا الفارق، ثم استقبل القبلة ورفع يديه يدعو ربه ويلح في الدعاء: «اللهم أنجز لي ما وعدتني».

استمر ﷺ في الدعاء حتى سقط رداؤه عن منكبيه، فجاء أبو بكر رضي الله عنه وردّ الرداء على كتفيه وطمأنه بأن الله سينجز له ما وعده.

وجاءت الاستجابة كما يذكر القرآن: ﴿إِذْ تَسْتَغِيثُونَ رَبَّكُمْ فَاسْتَجَابَ لَكُمْ﴾.

ثم بقي ذكر بدر في القرآن شاهدًا على هذا اليوم: ﴿وَلَقَدْ نَصَرَكُمُ اللَّهُ بِبَدْرٍ وَأَنتُمْ أَذِلَّةٌ﴾.

وتختصر آية أخرى المعنى الذي تحمله هذه المحطة: ﴿وَمَا النَّصْرُ إِلَّا مِنْ عِندِ اللَّهِ الْعَزِيزِ الْحَكِيمِ﴾.
```

## Provenance changes

Four provenance links were added; no existing provenance row was removed or modified.

| New provenance row ID | Station / content ID | Source ID | Provenance reference | Local passage ID |
|---:|---|---:|---|---|
| 857 | HIJRAH-01 / 22 | 2 | Sahih al-Bukhari 3653 | `c94fa68dbed289d05f61130799a321b97a30f495` |
| 858 | HIJRAH-01 / 22 | 2 | Sahih al-Bukhari 3922 | `468f5613230814f1f0e7e5b443dd19dcb88efd85` |
| 859 | BADR-01 / 28 | 30 | Quran 8:9 | `94aa7fd04884d5f7187fee705e5136ecb776fa1e` |
| 860 | BADR-01 / 28 | 5 | muslim:4588 | `3c86805857572b26ec877bf011d83b7476e30c18` |

New provenance rows are marked `reviewed` because the local reference-to-passage mapping was checked; their rights status remains `needs_review`. The source registry itself was unchanged: Bukhari, Muslim, and Quran source records remain `unverified` / `needs_review` / `APPROVED_LEVEL_2`. No record was marked verified or rights-cleared.

## Database integrity

| Table | Before | After story install | After the three demo taps |
|---|---:|---:|---:|
| `public.passages` | 166,774 | 166,774 | 166,774 |
| `app.embeddings` | 13 | 13 | 13 |
| `app.stations` | 14 | 14 | 14 |
| `app.station_passages` | 58 | 58 | 58 |
| `app.station_content` | 75 | 75 | 75 |
| `app.station_content_provenance` | 280 | 284 | 284 |
| `app.interactions` | 22 | 22 | 25 |

All 75 `app.station_content` rows were compared within the install transaction. Only the title/body fields of IDs 16, 22, and 28 differed; every other row and every other field matched. The 13 `app.station_passages` links attached to these three stations matched their pre-edit snapshot; total station-passage links remained 58. The three API taps each used a stable request ID, and the request-ID check found exactly three rows.

Complete ordered-row fingerprints matched before and after the install transaction: `public.passages` `f21077443984dfaa0a1df0e78e1633b8`; `app.embeddings` `af7aa635812345144addaccf2aa2ef14`. These tables were not written.

All stored story strings passed a UTF-8 encode/decode round trip and contained no Unicode replacement character. BADR-01 begins “نصل في هذه المحطة إلى يوم بدر.” and no longer begins with the old “يذكر القرآن الكريم بدرًا صراحة...” text. WAHY and HIJRAH begin with their required approved prefixes.

## Provider and tests

The normal station route was exercised through the real FastAPI endpoint and PostgreSQL. The provider factory was replaced with a guard that would fail if called; all three routes passed and the call count remained zero. No Gemini request, migration, `load_to_db.py`, passage write, or embedding write was performed.

Automated non-destructive suite: **60 passed, 1 skipped**. The opt-in read-only database trust audit was run separately with `KHUTA_DB_AUDIT=1`: **1 passed**. The database integration fixture was excluded because it mutates and deletes fixture rows. Two existing FastAPI lifecycle deprecation warnings were reported; no failures.

## Final verdict

PASS — THREE DEMO STORIES READY

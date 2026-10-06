"""Idempotently install evidence-mapped visitor Master Content.

Only app.station_content and app.station_content_provenance are written. Existing
content bodies, passages, station links, embeddings, visitors, and interactions are
preserved. Quran text remains Arabic source evidence; English is labelled as an
educational adaptation and never represented as an authoritative translation.
"""

import asyncio
import json
from dataclasses import dataclass
from sqlalchemy import text

from app.db.session import engine

QURAN_SOURCE = "\u0645\u0635\u062d\u0641 \u062d\u0641\u0635"
HADITH_SOURCE = "quranlab/hadith:bukhari-ar"
STALE_QURAN_397_ID = "22c982ca1b1d478ec600bd3f3ad310a70d4afbd"
VERIFIED_QURAN_397_ID = "22c982ca1b1d478ec600bd3f3ad310a70d4afbd5"
LEVELS = ("beginner", "intermediate", "advanced")


@dataclass(frozen=True)
class Evidence:
    passage_id: str
    reference: str
    content_type: str = "quran"
    source: str = QURAN_SOURCE
    lang: str = "ar"
    linked_station: str | None = None


def q(pid: str, ref: str, station: str | None = None) -> Evidence:
    return Evidence(pid, ref, linked_station=station)


def h(pid: str, ref: str, station: str) -> Evidence:
    return Evidence(pid, ref, "hadith", HADITH_SOURCE, "ar", station)


# Each body's claims are mapped to every listed passage. The content is the same
# factual set at each level; only sentence length and source-context wording vary.
CONTENT = {
    "TAWHEED-01": {
        "title_ar": "\u0627\u0644\u062a\u0648\u062d\u064a\u062f",
        "title_en": "Educational adaptation — Tawheed",
        "evidence": [
            q("04a8e5875c8495fdc6502f4d31d409fc030e2f3d", "112:1"),
            q("4afd60c7cf301fcf1cbf2bd0558745e3f461ddef", "2:163"),
            q("4aa2ce614f93de1780dc2f465230e98fce1d3e8a", "6:102"),
            q("15c955999e9a5ae9291110c1497be59a3b953175", "65:3"),
            q("8f24fd47cba4d61e47e1d1221a8ec5fd5ebbda57", "14:7"),
        ],
        "ar": {
            "beginner": "في سورة الإخلاص، يصف القرآن الله بأنه أحد. وتدعو آيات أخرى إلى عبادة الله، وتذكره خالقًا لكل شيء. كما تذكر آياتٌ التوكل عليه وشكره في سياقها.",
            "intermediate": "تعرض الآيات معاني محددة: يصف القرآن الله بأنه أحد، ويدعو إلى عبادته، ويذكره خالقًا لكل شيء. كما يرد ذكر التوكل والشكر في سياق آيتيهما.",
            "advanced": "تجمع هذه الآيات بين وصف الله بالأحد، والدعوة إلى عبادته وذكره خالقًا لكل شيء، ثم التوكل عليه والشكر في موضعيهما. يقتصر العرض على هذه المعاني الواردة في الآيات المختارة.",
        },
        "en": {
            "beginner": "In Surah Al-Ikhlas, the Quran describes Allah as One. Other verses call people to worship Allah and describe Him as Creator. The Quran also mentions reliance on Allah and gratitude in the context of those verses.",
            "intermediate": "The selected verses describe Allah as One, call people to worship Him, and describe Him as Creator. They also mention reliance on Allah and gratitude in their respective contexts.",
            "advanced": "These selected verses bring together the description of Allah as One, worship directed to Him, and His description as Creator, alongside reliance and gratitude in their stated contexts. This adaptation stays within those cited themes.",
        },
    },
    "KAABA-01": {
        "title_ar": "\u0627\u0644\u0643\u0639\u0628\u0629 \u0648\u0627\u0644\u0628\u064a\u062a \u0627\u0644\u062d\u0631\u0627\u0645",
        "title_en": "Educational adaptation — The Kaaba",
        "evidence": [
            q("72f41d9ecaab12efc8683418a64f795648f86d1e", "3:96"),
            q("dd0a7a5f953b980556c78bf66977eb2f9cfc4cd9", "2:127"),
            q("e254f72217ac0269fb3843691dfbc8451a0c8ff0", "2:144"),
            q(VERIFIED_QURAN_397_ID, "3:97"),
        ],
        "ar": {
            "beginner": "يذكر القرآن البيت في بكة، ويذكر أن إبراهيم وإسماعيل رفعا قواعد البيت. كما يوجّه إلى المسجد الحرام في الصلاة، ويربط البيت بالحج لمن استطاع إليه سبيلًا.",
            "intermediate": "يذكر القرآن البيت في بكة ورفع إبراهيم وإسماعيل قواعده. وتتناول آيات أخرى التوجه إلى المسجد الحرام في الصلاة والحج لمن استطاع إليه سبيلًا.",
            "advanced": "تربط الآيات المختارة البيت ببكة، ورفع إبراهيم وإسماعيل قواعده، والتوجه إلى المسجد الحرام في الصلاة، والحج لمن استطاع إليه سبيلًا. لا تتناول هذه الصياغة تاريخ البناء أو تفاصيله.",
        },
        "en": {
            "beginner": "The Quran mentions the House at Bakkah and says that Ibrahim and Ismail raised its foundations. It also directs prayer toward al-Masjid al-Haram and connects the House with pilgrimage for those able to undertake it.",
            "intermediate": "The Quran connects the House at Bakkah with Ibrahim and Ismail raising its foundations. Other cited verses address the prayer direction toward al-Masjid al-Haram and pilgrimage for those able to undertake it.",
            "advanced": "The selected verses connect the House at Bakkah, Ibrahim and Ismail raising its foundations, the prayer direction toward al-Masjid al-Haram, and pilgrimage for those able to undertake it. They do not establish architectural dates or a construction history.",
        },
    },
    "SALAH-01": {
        "title_ar": "\u0627\u0644\u0635\u0644\u0627\u0629",
        "title_en": "Educational adaptation — Prayer",
        "evidence": [
            q("b724367b4e4cb25d8fae0d30e31c15976441502f", "2:43"),
            q("7b097c45df113a0f77a3b0a09bdcd2d721f1e7be", "20:14"),
            q("3d4409c4a67378b955e6d3cf31f224802a0a6320", "4:103"),
            q("1ddd1aba66388e06518dd530f2be9e65be4b2664", "11:114"),
            q("7f8cd737b04f4b85415f32ae379b4b292226704b", "29:45"),
        ],
        "ar": {
            "beginner": "تدعو آيات القرآن إلى إقامة الصلاة، وتربط إحداها الصلاة بذكر الله. وتشير آيات أخرى إلى أوقاتها وإلى أثرها في سياقها.",
            "intermediate": "تأمر الآيات بإقامة الصلاة، وتذكر الصلاة للذكر، وتشير إلى أوقاتها. كما تصف آية أثر الصلاة في سياقها.",
            "advanced": "تتناول الآيات المختارة إقامة الصلاة والذكر وأوقاتها، وتورد آيةٌ أثرًا للصلاة في سياقها. يقتصر هذا العرض على هذه الموضوعات ولا يقدم شرحًا فقهيًا لطريقة الأداء.",
        },
        "en": {
            "beginner": "The Quran calls people to establish prayer, and one verse connects prayer with remembering Allah. Other cited verses refer to prayer times and describe its effect in context.",
            "intermediate": "The selected verses command prayer, connect it with remembrance, and refer to its times. Another cited verse describes an effect of prayer in its context.",
            "advanced": "The selected verses address establishing prayer, remembrance, and prayer times; another states an effect of prayer in its context. This is an educational overview, not a guide to legal details or ritual differences.",
        },
    },
    "SEERAH-01": {
        "title_ar": "\u0631\u062d\u0644\u0629 \u062a\u0645\u0647\u064a\u062f\u064a\u0629 \u0641\u064a \u0627\u0644\u0633\u064a\u0631\u0629",
        "title_en": "Educational adaptation — Seerah journey",
        "evidence": [
            q("4501640cbf4bf52e349fb9ea12c1bb2fec492289", "96:1", "WAHY-01"),
            h("bb9bec5713b6f005ee24fefeaf49ad4c95cc9a77", "bukhari:3", "WAHY-01"),
            q("b1fc3f4c375823406cd257241fed68300c9e4af3", "9:40", "HIJRAH-01"),
            h("2d5eb2f7011c3908572dc9e99eeab9ac0231da99", "bukhari:5807", "HIJRAH-01"),
            q("74a24002de6cb4e43a98b054fab0130e1543019f", "3:123", "BADR-01"),
        ],
        "ar": {
            "beginner": "تجمع هذه المحطة ثلاثة تجارب مستقلة: بداية الوحي، والهجرة، وبدر. لكل موضوع محطة متخصصة تعرض أدلتها المحددة؛ اختر إحداها للمتابعة.",
            "intermediate": "تعمل هذه المحطة مدخلًا إلى ثلاث تجارب منفصلة: بداية الوحي، والهجرة، وبدر. تعرض محطات الوحي والهجرة وبدر أدلتها الخاصة، ويمكن للزائر اختيار ما يريد استكشافه.",
            "advanced": "هذه المحطة بوابة تعريفية، لا سيرة كاملة؛ وهي تصل الزائر بتجارب بداية الوحي والهجرة وبدر في محطاتها المتخصصة. تبقى التفاصيل والأدلة ضمن كل محطة، ولا تقترح هذه الصياغة تسلسلًا زمنيًا شاملًا.",
        },
        "en": {
            "beginner": "This station introduces three separate experiences: the beginning of revelation, the Hijrah, and Badr. Each topic has a specialist station with its own evidence; choose one to continue.",
            "intermediate": "This station is an entry point to three separate experiences: the beginning of revelation, the Hijrah, and Badr. The specialist stations present their own evidence, and visitors can choose which to explore.",
            "advanced": "This is an orientation hub, not a complete Seerah. It points visitors to separate experiences on the beginning of revelation, the Hijrah, and Badr; detailed accounts and evidence remain in those stations, without asserting a complete chronology.",
        },
    },
    "HISTORY-01": {
        "title_ar": "\u0644\u0645\u062d\u0627\u062a \u062a\u0627\u0631\u064a\u062e\u064a\u0629 \u0645\u062d\u062f\u0648\u062f\u0629",
        "title_en": "Educational adaptation — Historical vignettes",
        "evidence": [
            q("435ba0f0aeffca6f37adca2e7811f028c5ae5e29", "33:9"),
            q("9add97cc5205c0a0daeb3014e1dc7177c5291820", "33:22"),
            q("bc2a89a87fec2e5dec837fff9d8859c931ddbd9d", "48:18"),
        ],
        "ar": {
            "beginner": "تذكر آيات القرآن أحداثًا منها الأحزاب والبيعة تحت الشجرة. هذه لمحات محدودة، وليست تسلسلًا كاملًا لتاريخ الإسلام.",
            "intermediate": "تتناول الآيات المختارة ما ورد عن الأحزاب والبيعة تحت الشجرة. وهي أمثلة محدودة لا تقدم خطًا زمنيًا شاملًا لتاريخ الإسلام.",
            "advanced": "تعرض الآيات المختارة إشارات إلى الأحزاب وإلى البيعة تحت الشجرة. يقتصر نطاق المحطة على هذه اللمحات الموثقة، ولا يدعي تقديم تاريخ شامل أو ترتيب زمني كامل.",
        },
        "en": {
            "beginner": "The Quran mentions events that include the Confederates and the pledge under the tree. These are limited glimpses, not a complete timeline of Islamic history.",
            "intermediate": "The selected verses refer to the Confederates and the pledge under the tree. They are bounded examples, not a comprehensive timeline of Islamic history.",
            "advanced": "The selected verses contain references to the Confederates and the pledge under the tree. This station is limited to these evidence-bounded vignettes and does not claim a complete history or chronology.",
        },
    },
    "WUDU-01": {
        "title_ar": "\u0627\u0644\u0648\u0636\u0648\u0621 \u0641\u064a \u0627\u0644\u0642\u0631\u0622\u0646",
        "title_en": "Educational adaptation — Wudu",
        "evidence": [
            q("93737e175c4ed093d8fd976e0dea854594cfcd7a", "5:6"),
            q("36bd95bdd6a0e31763bd46642ad5ae8ddc241f15", "4:43"),
        ],
        "ar": {
            "beginner": "تذكر آية الوضوء غسل الوجه واليدين إلى المرافق، ومسح الرأس، وغسل القدمين. كما تذكر الآيات المختارة سياقات أخرى؛ وهذا العرض لا يقدم حكمًا لحالة شخصية.",
            "intermediate": "تورد آية الوضوء غسل الوجه واليدين إلى المرافق ومسح الرأس وغسل القدمين، وتذكر الآيات المختارة سياقات أخرى للطهارة. يقتصر الشرح على النص ولا يفصل الأحكام الفقهية.",
            "advanced": "تسجل الآيات المختارة أفعال الوضوء المذكورة في 5:6، وتعرض سياقات الطهارة الواردة في 5:6 و4:43. لا تستخلص هذه المحطة دليلًا لحالة فردية ولا تعرض تفصيلًا فقهيًا.",
        },
        "en": {
            "beginner": "The Quran’s ablution verse mentions washing the face and arms to the elbows, wiping the head, and washing the feet. The selected verses also mention other contexts; this exhibit does not give a ruling for a personal case.",
            "intermediate": "The ablution verse names washing the face and arms to the elbows, wiping the head, and washing the feet, while the selected verses mention other purification contexts. This explanation stays with the text and does not detail jurisprudential rulings.",
            "advanced": "The selected verses record the ablution actions stated in 5:6 and purification contexts in 5:6 and 4:43. This station does not resolve individual cases or present detailed jurisprudence.",
        },
    },
    "ZAKAT-01": {
        "title_ar": "\u0627\u0644\u0632\u0643\u0627\u0629 \u0641\u064a \u0627\u0644\u0642\u0631\u0622\u0646",
        "title_en": "Educational adaptation — Zakat",
        "evidence": [
            q("b724367b4e4cb25d8fae0d30e31c15976441502f", "2:43"),
            q("6d81eeb67a7e222f5bec6a792fb1226c6a2dcc53", "2:110"),
            q("3fb9bdf2b40ab47576479b04ee51452ac5285200", "9:60"),
            q("c2b316a000a2e40a2e1441cb525a6437a1e94936", "9:103"),
        ],
        "ar": {
            "beginner": "تقرن آيات القرآن الزكاة بالصلاة. وتذكر آية أصنافًا للمستحقين، كما تذكر آية أخرى الصدقة والتطهير في سياقها. لا يحسب هذا العرض زكاة شخص بعينه.",
            "intermediate": "تأمر آيات بإقامة الصلاة وإيتاء الزكاة، وتذكر آية أصنافًا للمستحقين. وتتناول آية أخرى الصدقة والتطهير في سياقها؛ ولا يتضمن العرض حسابًا فرديًا.",
            "advanced": "تربط الآيات المختارة الصلاة بالزكاة، وتذكر أصنافًا للمستحقين، وتورد معنى الصدقة والتطهير في سياق 9:103. لا تحدد هذه المحطة مقدارًا أو حكمًا ماليًا لشخص بعينه.",
        },
        "en": {
            "beginner": "Some Quran verses pair zakat with prayer. Another verse names recipient categories, and a verse about charity uses purification language in its context. This exhibit does not calculate an individual’s zakat.",
            "intermediate": "The cited verses command prayer and zakat, name recipient categories, and discuss charity with purification language in context. The exhibit does not calculate an individual amount.",
            "advanced": "The selected verses connect prayer and zakat, name recipient categories, and use purification language about charity in the context of 9:103. This station does not determine a personal amount or financial ruling.",
        },
    },
}

TITLES = {
    "TAWHEED-01": "Tawheed", "KAABA-01": "Kaaba", "SALAH-01": "Prayer",
    "SEERAH-01": "Seerah journey", "HISTORY-01": "Historical vignettes",
    "WUDU-01": "Wudu", "ZAKAT-01": "Zakat",
}


async def fetch_rows(conn, sql, params=None):
    return [dict(r) for r in (await conn.execute(text(sql), params or {})).mappings().all()]


async def table_count(conn, table):
    return int(await conn.scalar(text(f"select count(*) from {table}")))


async def validate_evidence(conn):
    source_cache = {}
    validated = {}
    for code, spec in CONTENT.items():
        station = (await conn.execute(text("select id from app.stations where code=:code"), {"code": code})).scalar_one_or_none()
        if station is None:
            raise RuntimeError(f"Missing station {code}")
        validated[code] = {"station_id": station, "evidence": []}
        for evidence in spec["evidence"]:
            row = (await conn.execute(text("""select id,type,lang,source,reference,surah,ayah,url,
                (text is not null and length(btrim(text))>0) as text_nonempty
                from public.passages where id=:id"""), {"id": evidence.passage_id})).mappings().one_or_none()
            if not row:
                raise RuntimeError(f"Missing evidence passage {evidence.passage_id} for {code}")
            row = dict(row)
            if (row["type"], row["lang"], row["source"], row["reference"], row["text_nonempty"]) != (
                evidence.content_type, evidence.lang, evidence.source, evidence.reference, True
            ):
                raise RuntimeError(f"Evidence validation mismatch for {code} {evidence.reference}")
            link_station = evidence.linked_station or code
            link_id = await conn.scalar(text("""select s.id from app.stations s join app.station_passages sp
                on sp.station_id=s.id where s.code=:code and sp.passage_id=:pid and sp.relationship_type='supports'"""),
                {"code": link_station, "pid": evidence.passage_id})
            if link_id is None:
                raise RuntimeError(f"Required evidence link missing: {link_station} {evidence.reference}")
            key = (evidence.source, evidence.content_type)
            if key not in source_cache:
                sources = await fetch_rows(conn, """select id,source_name,source_type,source_url,
                    verification_status,rights_status from app.content_sources
                    where source_name=:name and source_type=:type order by id""",
                    {"name": evidence.source, "type": evidence.content_type})
                if len(sources) != 1:
                    raise RuntimeError(f"Expected exactly one content source for {evidence.source}/{evidence.content_type}")
                source_cache[key] = sources[0]
            validated[code]["evidence"].append({"record": row, "source": source_cache[key], "linked_station": link_station})
    return validated


def source_note(lang):
    base = "Master Content for approved demo use; factual references are recorded in station_content_provenance. Dataset verification and reuse rights retain their existing registry status."
    if lang == "en":
        return base + " English is a visitor-facing educational adaptation from the Arabic master, not an authoritative Quran translation."
    return base + " Arabic is the primary Master Content language."


async def install():
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured")
    inserted_content = 0
    inserted_provenance = 0
    updated_english_labels = 0
    counts_before = {}
    async with engine.begin() as conn:
        counts_before = {
            "public.passages": await table_count(conn, "public.passages"),
            "app.embeddings": await table_count(conn, "app.embeddings"),
            "app.stations": await table_count(conn, "app.stations"),
            "app.station_passages": await table_count(conn, "app.station_passages"),
            "app.station_content": await table_count(conn, "app.station_content"),
            "app.station_content_provenance": await table_count(conn, "app.station_content_provenance"),
        }
        evidence = await validate_evidence(conn)
        station_ids = {code: row["station_id"] for code, row in evidence.items()}
        locked = await conn.execute(text("select id from app.stations where id=any(:ids) order by id for update"),
            {"ids": list(station_ids.values())})
        if len(locked.all()) != len(station_ids):
            raise RuntimeError("Station lock/preflight did not resolve every station")

        # QURAN-01 already has six controlled rows. Preserve every title/body and
        # label only its existing English source_note as an educational adaptation.
        quran_id = await conn.scalar(text("select id from app.stations where code='QURAN-01'"))
        english_rows = await fetch_rows(conn, "select id,source_note from app.station_content where station_id=:id and lang='en' order by id", {"id": quran_id})
        if len(english_rows) != 3:
            raise RuntimeError(f"Expected three existing QURAN-01 English level rows; found {len(english_rows)}")
        label = "English visitor-facing educational adaptation; not an authoritative Quran translation."
        for row in english_rows:
            note = row["source_note"] or ""
            if label not in note:
                await conn.execute(text("update app.station_content set source_note=:note where id=:id"),
                    {"id": row["id"], "note": f"{note} {label}".strip()})
                updated_english_labels += 1

        for code, spec in CONTENT.items():
            sid = station_ids[code]
            for lang in ("ar", "en"):
                title = spec["title_ar"] if lang == "ar" else spec["title_en"]
                for level in LEVELS:
                    body = spec[lang][level]
                    current = (await conn.execute(text("""select id,title,body,source_note from app.station_content
                        where station_id=:sid and lang=:lang and level=:level and title=:title"""),
                        {"sid": sid, "lang": lang, "level": level, "title": title})).mappings().one_or_none()
                    if current:
                        if current["body"] != body or current["source_note"] != source_note(lang):
                            raise RuntimeError(f"Conflicting existing Master Content row for {code}/{lang}/{level}")
                        content_id = current["id"]
                    else:
                        content_id = await conn.scalar(text("""insert into app.station_content
                            (station_id,lang,level,title,body,source_note)
                            values(:sid,:lang,:level,:title,:body,:note) returning id"""),
                            {"sid": sid, "lang": lang, "level": level, "title": title,
                             "body": body, "note": source_note(lang)})
                        inserted_content += 1

                    for item in evidence[code]["evidence"]:
                        p = item["record"]
                        src = item["source"]
                        prov = (await conn.execute(text("""select id,passage_id,source_url,verification_status,rights_status
                            from app.station_content_provenance where station_content_id=:cid and source_id=:source and reference=:ref"""),
                            {"cid": content_id, "source": src["id"], "ref": p["reference"]})).mappings().one_or_none()
                        expected = (p["id"], p["url"], src["verification_status"], src["rights_status"])
                        if prov:
                            actual = (prov["passage_id"], prov["source_url"], prov["verification_status"], prov["rights_status"])
                            if actual != expected:
                                raise RuntimeError(f"Conflicting provenance for {code}/{lang}/{level}/{p['reference']}")
                            continue
                        notes = "Exact local source/type/reference mapping; source verification and reuse rights are not independently established."
                        if lang == "en":
                            notes += " English body is an educational adaptation from the Arabic master."
                        await conn.execute(text("""insert into app.station_content_provenance
                            (station_content_id,source_id,reference,source_url,verification_status,rights_status,
                             retrieved_at,notes,passage_id)
                            values(:cid,:source,:ref,:url,:verification,:rights,null,:notes,:pid)"""),
                            {"cid": content_id, "source": src["id"], "ref": p["reference"], "url": p["url"],
                             "verification": src["verification_status"], "rights": src["rights_status"],
                             "notes": notes, "pid": p["id"]})
                        inserted_provenance += 1

        counts_after = {
            "public.passages": await table_count(conn, "public.passages"),
            "app.embeddings": await table_count(conn, "app.embeddings"),
            "app.stations": await table_count(conn, "app.stations"),
            "app.station_passages": await table_count(conn, "app.station_passages"),
            "app.station_content": await table_count(conn, "app.station_content"),
            "app.station_content_provenance": await table_count(conn, "app.station_content_provenance"),
        }
        for immutable in ("public.passages", "app.embeddings", "app.stations", "app.station_passages"):
            if counts_after[immutable] != counts_before[immutable]:
                raise RuntimeError(f"Immutable table count changed unexpectedly: {immutable}")
        if counts_after["app.station_content"] != counts_before["app.station_content"] + inserted_content:
            raise RuntimeError("station_content count delta does not match inserted rows")
        if counts_after["app.station_content_provenance"] != counts_before["app.station_content_provenance"] + inserted_provenance:
            raise RuntimeError("provenance count delta does not match inserted rows")

    print(json.dumps({"before": counts_before, "after": counts_after,
        "content_rows_inserted": inserted_content, "provenance_rows_inserted": inserted_provenance,
        "quran_english_source_notes_updated": updated_english_labels}, ensure_ascii=True))


if __name__ == "__main__":
    asyncio.run(install())

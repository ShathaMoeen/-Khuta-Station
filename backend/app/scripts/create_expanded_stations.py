"""Idempotently create the seven approved visitor-facing station records.

This operation only inserts app.stations and app.station_passages rows. It never
edits passages, embeddings, existing stations, station content, provenance, or links.
Evidence links are accepted only when the requested passage ID matches the expected
Quran reference, Arabic language, type, and the existing Quran source.
"""

import argparse
import asyncio
import json
from collections import Counter
from sqlalchemy import text

from app.db.session import engine

STATIONS = (
    ("TAWHEED-01", "\u0627\u0644\u062a\u0648\u062d\u064a\u062f", "Tawheed", "Gallery A"),
    ("KAABA-01", "\u0627\u0644\u0643\u0639\u0628\u0629", "Kaaba", "Gallery A"),
    ("SALAH-01", "\u0627\u0644\u0635\u0644\u0627\u0629", "Prayer", "Gallery A"),
    ("SEERAH-01", "\u0627\u0644\u0633\u064a\u0631\u0629", "Seerah", "Gallery A"),
    ("HISTORY-01", "\u0627\u0644\u062a\u0627\u0631\u064a\u062e", "Islamic History", "Gallery A"),
    ("WUDU-01", "\u0627\u0644\u0648\u0636\u0648\u0621", "Wudu", "Gallery A"),
    ("ZAKAT-01", "\u0627\u0644\u0632\u0643\u0627\u0629", "Zakat", "Gallery A"),
)
QURAN_SOURCE = "\u0645\u0635\u062d\u0641 \u062d\u0641\u0635"
REFERENCE_LINKS = {
    "TAWHEED-01": {
        "112:1": "04a8e5875c8495fdc6502f4d31d409fc030e2f3d",
        "112:2": "2251d4eb44e905148dc3b90981bf7ff8707d49f9",
        "112:3": "0cb6641828cb2e8783f3ba529ae6c3dde333261c",
        "112:4": "547014de91a9af026cb4118943c13f2c69c9d0fd",
        "2:163": "4afd60c7cf301fcf1cbf2bd0558745e3f461ddef",
        "6:102": "4aa2ce614f93de1780dc2f465230e98fce1d3e8a",
        "16:36": "1b7af94d1cf44d02513d925873ebc091e17c8816",
        "21:25": "5d465ae22360b40c539d2fe3e0d9e13f195c279c",
        "51:56": "a319d939d12f05315e2e5a77e616ec7d10f7c0f6",
        "65:3": "15c955999e9a5ae9291110c1497be59a3b953175",
        "14:7": "8f24fd47cba4d61e47e1d1221a8ec5fd5ebbda57",
    },
    "KAABA-01": {
        "2:125": "bbe35b28cd92a2cc052e9e5df436f36a6fb31bfe",
        "2:127": "dd0a7a5f953b980556c78bf66977eb2f9cfc4cd9",
        "2:144": "e254f72217ac0269fb3843691dfbc8451a0c8ff0",
        "3:96": "72f41d9ecaab12efc8683418a64f795648f86d1e",
        "3:97": "22c982ca1b1d478ec600bd3f3ad310a70d4afbd5",
        "22:26": "521d22902e94e311146c208f438a7bdf1f58c9f5",
        "22:27": "4dcbddcec85857a6724a250e21069d4b6d41d04b",
        "22:28": "d8a548dddf770957a6feff7825ea1ddf0232cc9d",
        "22:29": "54bd69793316e4b397fc07a84c10b59a9ac985fd",
        "14:37": "8ff07ed91297a48d83ca85697eb262e22d121056",
    },
    "SALAH-01": {
        "2:43": "b724367b4e4cb25d8fae0d30e31c15976441502f",
        "20:14": "7b097c45df113a0f77a3b0a09bdcd2d721f1e7be",
        "4:103": "3d4409c4a67378b955e6d3cf31f224802a0a6320",
        "11:114": "1ddd1aba66388e06518dd530f2be9e65be4b2664",
        "17:78": "06a1100c7b1b0decc75055a794e68c17504948c9",
        "29:45": "7f8cd737b04f4b85415f32ae379b4b292226704b",
        "2:110": "6d81eeb67a7e222f5bec6a792fb1226c6a2dcc53",
    },
    # SEERAH-01 is an overview hub. station_passages does not require a link;
    # specialized evidence remains on WAHY-01, HIJRAH-01, and BADR-01.
    "HISTORY-01": {
        "33:9": "435ba0f0aeffca6f37adca2e7811f028c5ae5e29",
        "33:22": "9add97cc5205c0a0daeb3014e1dc7177c5291820",
        "48:18": "bc2a89a87fec2e5dec837fff9d8859c931ddbd9d",
    },
    "WUDU-01": {
        "5:6": "93737e175c4ed093d8fd976e0dea854594cfcd7a",
        "4:43": "36bd95bdd6a0e31763bd46642ad5ae8ddc241f15",
    },
    "ZAKAT-01": {
        "2:43": "b724367b4e4cb25d8fae0d30e31c15976441502f",
        "2:110": "6d81eeb67a7e222f5bec6a792fb1226c6a2dcc53",
        "9:60": "3fb9bdf2b40ab47576479b04ee51452ac5285200",
        "9:103": "c2b316a000a2e40a2e1441cb525a6437a1e94936",
        "9:71": "5cc1aaeb272a9e5d59e23c3e4687a1ed78afb2be",
        "2:177": "15957d18591c89eeaa540caf32525c81995c8411",
    },
}
PROTECTED_CODES = ("ST-01", "ST-02", "QURAN-01", "WAHY-01", "HIJRAH-01", "BADR-01", "HADITH-01")


async def count(conn, table):
    return int(await conn.scalar(text(f"select count(*) from {table}")))


async def snapshot_rows(conn, sql, params=None):
    rows = (await conn.execute(text(sql), params or {})).mappings().all()
    return [dict(row) for row in rows]


async def run():
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured")
    expected = {code: (name, topic, location) for code, name, topic, location in STATIONS}
    skipped = []
    added_stations = 0
    added_links = 0
    before = {}

    async with engine.begin() as conn:
        before = {
            "public.passages": await count(conn, "public.passages"),
            "app.embeddings": await count(conn, "app.embeddings"),
            "app.stations": await count(conn, "app.stations"),
            "app.station_passages": await count(conn, "app.station_passages"),
            "app.station_content": await count(conn, "app.station_content"),
            "app.station_content_provenance": await count(conn, "app.station_content_provenance"),
        }
        existing = await snapshot_rows(conn, "select id, code, name, topic, location from app.stations")
        by_code = {row["code"]: row for row in existing}
        conflicts = []
        for code, wanted in expected.items():
            row = by_code.get(code)
            if row and (row["name"], row["topic"], row["location"]) != wanted:
                conflicts.append({"code": code, "existing_id": row["id"], "field_conflict": True})
        if conflicts:
            raise RuntimeError(f"Existing station code conflict; no writes performed: {conflicts}")
        if not by_code.get("QURAN-01"):
            raise RuntimeError("QURAN-01 is missing; no writes performed")

        baseline = await conn.scalar(text("select source from public.passages where id='4501640cbf4bf52e349fb9ea12c1bb2fec492289' and type='quran' and reference='96:1'"))
        if baseline != QURAN_SOURCE:
            raise RuntimeError("Existing Quran source baseline did not match expected source; no writes performed")

        validated = []
        for code, refs in REFERENCE_LINKS.items():
            for ref, passage_id in refs.items():
                row = (await conn.execute(text("""select id,type,lang,source,reference
                    from public.passages where id=:id"""), {"id": passage_id})).mappings().one_or_none()
                if not row:
                    skipped.append({"station": code, "reference": ref, "passage_id": passage_id, "reason": "passage_id_not_found"})
                    continue
                if (row["type"], row["lang"], row["source"], row["reference"]) != ("quran", "ar", QURAN_SOURCE, ref):
                    skipped.append({"station": code, "reference": ref, "passage_id": passage_id, "reason": "type_language_source_or_reference_mismatch"})
                    continue
                validated.append((code, ref, passage_id))

        for code, name, topic, location in STATIONS:
            result = await conn.execute(text("""insert into app.stations(code,name,topic,location)
                values(:code,:name,:topic,:location) on conflict(code) do nothing returning id"""),
                {"code": code, "name": name, "topic": topic, "location": location})
            if result.scalar_one_or_none() is not None:
                added_stations += 1

        station_ids = dict((await conn.execute(text("select code,id from app.stations where code=any(:codes)"),
            {"codes": list(expected)})).all())
        if len(station_ids) != len(STATIONS):
            raise RuntimeError("Not all requested stations are present after insert")

        for code, ref, passage_id in validated:
            sid = station_ids[code]
            existing_link = await conn.execute(text("select id,relationship_type from app.station_passages where station_id=:sid and passage_id=:pid"),
                {"sid": sid, "pid": passage_id})
            if existing_link.first() is not None:
                continue
            result = await conn.execute(text("""insert into app.station_passages
                (station_id,passage_id,relationship_type,priority,notes)
                values(:sid,:pid,'supports',1.0000,:notes)
                on conflict(station_id,passage_id,relationship_type) do nothing returning id"""),
                {"sid": sid, "pid": passage_id, "notes": f"Exact local source and reference match for Quran {ref}."})
            if result.scalar_one_or_none() is not None:
                added_links += 1

        after = {
            "public.passages": await count(conn, "public.passages"),
            "app.embeddings": await count(conn, "app.embeddings"),
            "app.stations": await count(conn, "app.stations"),
            "app.station_passages": await count(conn, "app.station_passages"),
            "app.station_content": await count(conn, "app.station_content"),
            "app.station_content_provenance": await count(conn, "app.station_content_provenance"),
        }
        if after["public.passages"] != before["public.passages"] or after["app.embeddings"] != before["app.embeddings"]:
            raise RuntimeError("Protected passage or embedding count changed; transaction rolled back")
        if after["app.station_content"] != before["app.station_content"] or after["app.station_content_provenance"] != before["app.station_content_provenance"]:
            raise RuntimeError("Station content or provenance changed; transaction rolled back")

        protected_after = await snapshot_rows(conn, """select id,code,name,topic,location from app.stations
            where code=any(:codes) order by code""", {"codes": list(PROTECTED_CODES)})
        protected_before = {row["code"]: row for row in existing if row["code"] in PROTECTED_CODES}
        if protected_before != {row["code"]: row for row in protected_after}:
            raise RuntimeError("A protected existing station changed; transaction rolled back")

        station_summary = await snapshot_rows(conn, """select s.id,s.code,s.name,s.topic,s.location,count(sp.id)::int as link_count
            from app.stations s left join app.station_passages sp on sp.station_id=s.id
            group by s.id,s.code,s.name,s.topic,s.location order by s.id""")
        result = {
            "before": before,
            "after": after,
            "stations_inserted": added_stations,
            "links_inserted": added_links,
            "skipped_links": skipped,
            "station_inventory": station_summary,
        }

    print(json.dumps(result, ensure_ascii=True, default=str))


if __name__ == "__main__":
    asyncio.run(run())

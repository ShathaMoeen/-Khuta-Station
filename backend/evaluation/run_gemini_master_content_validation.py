"""Sequential live personalization checks through KHUTA's real station flow.

This intentionally retains test visitor/tap/generated-content rows and reports
before/after counts; it never edits passages, embeddings, station content,
provenance, stations, or station-passage links.
"""
from __future__ import annotations

import asyncio
import json
import secrets
import sys
import time
from pathlib import Path

from sqlalchemy import text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.db.session import SessionFactory, engine
from app.station_flow import _content_evidence, _curated_content, process_station_tap, register_visitor

STATIONS = ["TAWHEED-01", "KAABA-01", "SALAH-01", "SEERAH-01", "HISTORY-01", "QURAN-01", "WUDU-01", "ZAKAT-01"]
CORE_PROFILES = [("ar", "beginner"), ("ar", "advanced"), ("en", "beginner"), ("en", "advanced")]
INTERMEDIATE_STATIONS = ["TAWHEED-01", "KAABA-01", "SEERAH-01", "HISTORY-01"]
MIN_REQUEST_INTERVAL = 15.0


async def counts(conn) -> dict[str, int]:
    tables = {
        "public.passages": "select count(*) from public.passages",
        "app.embeddings": "select count(*) from app.embeddings",
        "app.stations": "select count(*) from app.stations",
        "app.station_passages": "select count(*) from app.station_passages",
        "app.station_content": "select count(*) from app.station_content",
        "app.station_content_provenance": "select count(*) from app.station_content_provenance",
        "app.visitors": "select count(*) from app.visitors",
        "app.interactions": "select count(*) from app.interactions",
        "app.generated_content": "select count(*) from app.generated_content",
    }
    return {name: int((await conn.execute(text(query))).scalar_one()) for name, query in tables.items()}


async def run_case(language: str, level: str, station: str, card: str) -> dict:
    async with SessionFactory() as session:
        station_id = (await session.execute(text("select id from app.stations where code=:code"), {"code": station})).scalar_one()
        selected = await _curated_content(session, station_id, language, level)
        evidence = await _content_evidence(session, int(selected["id"])) if selected else []
        expected = sorted({(row["source"], row["reference"]) for row in evidence})
        request_id = "gmc-" + secrets.token_hex(12)
        response = await process_station_tap(session, card, station, request_id)
        sources = response.get("sources") or []
        actual = sorted({(row.get("source"), row.get("reference")) for row in sources})
        visitor = response.get("visitor") or {}
        content = response.get("content") or {}
        forbidden_keys = {"id", "passage_id", "source_id", "station_content_id", "score", "similarity", "rank", "hash"}
        exposed_keys = sorted(forbidden_keys.intersection(response.keys()))
        output = response.get("personalized_explanation") or ""
        return {
            "station": station, "language": language, "level": level,
            "gemini_called": bool(response.get("ai_generated")),
            "ai_generated": bool(response.get("ai_generated")), "ai_status": response.get("ai_status"),
            "selected_content_language": content.get("lang"), "selected_content_level": content.get("level"),
            "visitor_language": visitor.get("language"), "visitor_level": visitor.get("level"),
            "content_selected_correctly": content.get("lang") == language and content.get("level") == level,
            "answer_nonempty": bool(output.strip()), "citation_count": len(sources),
            "citations_match_selected_provenance": bool(sources) and set(actual).issubset(set(expected)),
            "expected_references": expected, "returned_references": actual,
            "no_internal_fields_exposed": not exposed_keys, "exposed_fields": exposed_keys,
            "explanation_source": response.get("explanation_source"), "answer": output,
        }


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    settings = get_settings()
    if settings.llm_provider != "gemini" or not settings.gemini_api_key:
        raise SystemExit("Live validation not started: Gemini provider is not configured.")
    result: dict = {"provider": settings.llm_provider, "model": settings.llm_model, "cases": [], "stopped_on_429": False}
    async with engine.connect() as conn:
        result["before"] = await counts(conn)
    profiles = CORE_PROFILES + [("ar", "intermediate"), ("en", "intermediate")]
    cards: dict[tuple[str, str], str] = {}
    cases = [(lang, level, station) for lang, level in CORE_PROFILES for station in STATIONS]
    cases += [(lang, "intermediate", station) for lang in ("ar", "en") for station in INTERMEDIATE_STATIONS]
    last_request = 0.0
    for index, (language, level, station) in enumerate(cases):
        profile_key = (language, level)
        if profile_key not in cards:
            card = "GMC-" + secrets.token_hex(8).upper()
            async with SessionFactory() as session:
                await register_visitor(session, language, level, True, card)
            cards[profile_key] = card
        delay = MIN_REQUEST_INTERVAL - (asyncio.get_running_loop().time() - last_request)
        if last_request and delay > 0:
            await asyncio.sleep(delay)
        case = await run_case(language, level, station, cards[profile_key])
        last_request = asyncio.get_running_loop().time()
        result["cases"].append(case)
        print(json.dumps({k: case[k] for k in ("station", "language", "level", "ai_generated", "ai_status", "answer_nonempty", "citation_count")}, ensure_ascii=False))
        if case.get("ai_status") == "gemini_rate_limited" or "HTTP 429" in str(case.get("ai_status")) or "quota" in str(case.get("ai_status", "")).lower():
            result["stopped_on_429"] = True
            result["not_tested_after_429"] = len(cases) - index - 1
            break
        await asyncio.sleep(0)
    async with engine.connect() as conn:
        result["after"] = await counts(conn)
    result["summary"] = {
        "planned_cases": len(cases), "attempted_cases": len(result["cases"]),
        "gemini_successes": sum(item["ai_generated"] for item in result["cases"]),
        "fallbacks": sum(not item["ai_generated"] for item in result["cases"]),
        "selection_passes": sum(item["content_selected_correctly"] for item in result["cases"]),
        "citation_passes": sum(item["citations_match_selected_provenance"] for item in result["cases"]),
        "nonempty_passes": sum(item["answer_nonempty"] for item in result["cases"]),
        "internal_field_passes": sum(item["no_internal_fields_exposed"] for item in result["cases"]),
    }
    output_path = Path(__file__).resolve().parent / "results" / "GEMINI_MASTER_CONTENT_LIVE_RESULTS.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "before": result["before"], "after": result["after"], "results_file": str(output_path)}, ensure_ascii=False))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

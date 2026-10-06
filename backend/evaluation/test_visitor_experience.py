"""Run a reversible simulated RFID visitor journey against the configured KHUTA DB.

Run from ``backend`` with ``python -m evaluation.test_visitor_experience``.
Only temporary visitors/interactions and previously-unassigned RFID mappings are
created; all are removed/restored in ``finally``. Gemini generation is
intentionally disabled for this deterministic check (the current account has
returned RESOURCE_EXHAUSTED); no fake answer is substituted.
"""
from __future__ import annotations

import json
import logging
import secrets
import sys
from datetime import datetime, timedelta, timezone
import psycopg
from fastapi.testclient import TestClient

from app.api import app, settings
from app.core.config import get_settings


def _dsn() -> str:
    dsn = get_settings().database_url
    if not dsn:
        raise RuntimeError("DATABASE_URL is not configured in backend/.env.")
    return dsn.replace("postgresql+asyncpg://", "postgresql://", 1)


def _citation_text(citations: list[dict]) -> str:
    return "; ".join(
        " — ".join(str(part) for part in (c.get("title"), c.get("reference")) if part)
        for c in citations
    ) or "No visitor-readable citations returned."


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    root_logger = logging.getLogger()
    old_log_level = root_logger.level
    root_logger.setLevel(logging.WARNING)
    dsn = _dsn()
    own_visitors: list[str] = []
    nonconsent_visitor = "KH-EVAL-NOCONSENT-" + secrets.token_hex(6).upper()
    assigned: list[tuple[int, str | None]] = []
    with psycopg.connect(dsn) as conn:
        baseline = {
            "passages": conn.execute("select count(*) from public.passages").fetchone()[0],
            "embeddings": conn.execute("select count(*) from app.embeddings").fetchone()[0],
            "links": conn.execute("select count(*) from app.station_passages").fetchone()[0],
        }
        rows = conn.execute("""select id,rfid_uid,card_id,language from app.rfid_cards
            where is_active is true and card_id is null order by id limit 4""").fetchall()
        if len(rows) != 4:
            raise RuntimeError("Need four active, currently-unassigned RFID records; no test writes were made.")
        # UID values are kept in memory only and never printed or written to reports.
        assigned = [(row[0], row[2]) for row in rows]
        uids = [row[1] for row in rows]
        card_languages = [row[3] for row in rows]
        badr_refs = set(conn.execute("""select p.source,p.reference from public.passages p
            join app.station_passages sp on sp.passage_id=p.id
            join app.stations s on s.id=sp.station_id
            where s.code='BADR-01' and sp.relationship_type='supports'""").fetchall())

    # Fail closed if any routine tries to call Gemini from this deterministic run.
    old_llm_key, old_embed_key = settings.gemini_api_key, settings.openai_api_key
    old_pgvector = settings.pgvector_enabled
    old_admin_key = settings.admin_api_key
    settings.gemini_api_key = None
    settings.openai_api_key = None
    settings.pgvector_enabled = False
    # The script authenticates its own assignment calls with a process-local key;
    # it does not change the user's configured secret or print this value.
    settings.admin_api_key = secrets.token_urlsafe(32)
    generated_by_level: dict[str, str] = {}
    citations_by_level: dict[str, set[tuple[str, str]]] = {}
    admin_headers = {"Authorization": f"Bearer {settings.admin_api_key}"}
    device_headers = ({"Authorization": f"Bearer {settings.device_api_key}"}
                      if settings.device_api_key else {})
    try:
        with TestClient(app) as client:
            print("=== KHUTA VISITOR EXPERIENCE (Gemini generation disabled for safe deterministic run) ===")
            print("Database health:", client.get("/health").json().get("database"))
            scenarios = (("ar", "beginner"), ("en", "beginner"),
                         ("en", "intermediate"), ("en", "advanced"))
            for index, ((language, level), tag_uid) in enumerate(zip(scenarios, uids)):
                created = client.post("/visitors", json={"lang": language, "level": level, "consent": True})
                if created.status_code != 200:
                    raise RuntimeError(f"Temporary visitor setup failed with HTTP {created.status_code}.")
                card_id = created.json()["card_id"]
                own_visitors.append(card_id)
                assign = client.post("/rfid/assign", headers=admin_headers,
                                     json={"rfid_uid": tag_uid, "card_id": card_id})
                if assign.status_code != 200:
                    raise RuntimeError(f"RFID assignment failed with HTTP {assign.status_code}.")
                if index == 0:
                    warmup = client.post("/rfid/tap", headers=device_headers,
                        json={"rfid_uid": tag_uid, "station_code": "WAHY-01",
                              "request_id": "visitor-eval-" + secrets.token_hex(12)})
                    if warmup.status_code != 200:
                        raise RuntimeError(f"Journey-history setup failed with HTTP {warmup.status_code}.")
                request_id = "visitor-eval-" + secrets.token_hex(12)
                tap = client.post("/rfid/tap", headers=device_headers,
                                  json={"rfid_uid": tag_uid, "station_code": "BADR-01", "request_id": request_id})
                if tap.status_code != 200:
                    raise RuntimeError(f"Simulated RFID tap failed with HTTP {tap.status_code}.")
                result = tap.json()
                visitor = result["visitor"]
                if visitor["language"] != language or visitor["level"] != level:
                    raise AssertionError("Tap did not use the visitor profile for language/level.")
                if index == 0 and ("WAHY-01" not in visitor["visited_stations"] or not visitor["interests"]):
                    raise AssertionError("Tap did not load prior station history and observed topics.")
                if result["content"]["level"] != level:
                    raise AssertionError("Station fallback does not match the requested visitor level.")
                if not result.get("recommended_station"):
                    raise AssertionError("Tap did not return a next-station recommendation.")
                if not result["sources"]:
                    raise AssertionError("Controlled Badr evidence/citations are missing.")
                if "\ufffd" in json.dumps(result, ensure_ascii=True):
                    raise AssertionError("Visitor response contains Unicode replacement characters.")
                tap_citations = {(s.get("source") or "", s.get("reference") or "") for s in result["sources"]}
                if not tap_citations.issubset(badr_refs):
                    raise AssertionError("Tap citation is not backed by a linked BADR-01 passage.")
                if language == "en":
                    citations_by_level[level] = tap_citations
                    generated_by_level[level] = result["personalized_explanation"]
                if any(k in json.dumps(result) for k in ("passage_id", "source_id", "vector", "score", "hash")):
                    raise AssertionError("Internal evidence identifiers or ranking data leaked to tap response.")
                replay = client.post("/rfid/tap", headers=device_headers,
                    json={"rfid_uid": tag_uid, "station_code": "BADR-01", "request_id": request_id})
                if replay.status_code != 200 or replay.json()["content"]["body"] != result["content"]["body"]:
                    raise AssertionError("A repeated RFID tap was not safely idempotent.")
                with psycopg.connect(dsn) as conn:
                    tap_count = conn.execute("""select count(*) from app.interactions i
                        join app.stations s on s.id=i.station_id
                        where i.card_id=%s and s.code='BADR-01'""", (card_id,)).fetchone()[0]
                if tap_count != 1:
                    raise AssertionError("Idempotent tap replay created a duplicate interaction.")
                if index == 1:
                    with psycopg.connect(dsn) as conn:
                        station_id = conn.execute("select id from app.stations where code='BADR-01'").fetchone()[0]
                    legacy_tap = client.post(f"/stations/{station_id}/interact", headers=device_headers,
                        json={"card_id": card_id, "request_id": "visitor-eval-" + secrets.token_hex(12)})
                    if legacy_tap.status_code != 200:
                        raise RuntimeError(f"Existing station interaction route failed with HTTP {legacy_tap.status_code}.")
                    legacy_result = legacy_tap.json()
                    if "interaction_id" in legacy_result or "id" in legacy_result.get("station", {}):
                        raise AssertionError("Existing station interaction route exposed internal database IDs.")
                    if "\ufffd" in json.dumps(legacy_result, ensure_ascii=True):
                        raise AssertionError("Existing station interaction route returned invalid Unicode.")
                if index == 0:
                    if client.get(f"/visitor/{card_id}").status_code != 200:
                        raise AssertionError("Consented visitor profile endpoint failed.")
                    if client.get(f"/visitor/{card_id}/report").status_code != 200:
                        raise AssertionError("Consented journey report endpoint failed.")
                    summary = client.get(f"/visitors/{card_id}/summary")
                    if summary.status_code != 200 or summary.json().get("stations_visited") != 2:
                        raise AssertionError("Consented visitor summary did not reflect the journey.")
                print(f"\n--- {language.upper()} {level.title()} visitor; station BADR-01 ---")
                print("Profile language:", visitor["language"], "| level:", visitor["level"])
                print("Presentation mode:", result["explanation_source"], "|", result["ai_status"])
                print(result["personalized_explanation"])
                print("Sources:", _citation_text(result["sources"]))

                # Exercise the normal follow-up endpoint. Hybrid/vector retrieval is
                # disabled locally; this invokes the production lexical retrieval and
                # governance path. Provider key is cleared, so no Gemini request occurs.
                ask = client.post("/ask", json={"card_id": card_id, "station_code": "BADR-01",
                    "question": "Tell me the story of the Battle of Badr."})
                if ask.status_code != 200:
                    raise RuntimeError(f"Follow-up route failed with HTTP {ask.status_code}.")
                ask_result = ask.json()
                print("Follow-up:", ask_result.get("status"), "|", ask_result.get("reason", ""))
                print("Sources:", _citation_text(ask_result.get("sources", [])))
                ask_citations = {(s.get("source") or "", s.get("reference") or "")
                                 for s in ask_result.get("sources", [])}
                if not ask_citations.issubset(badr_refs):
                    raise AssertionError("Ask citation is not backed by a linked BADR-01 passage.")
                if ask_result.get("answer"):
                    raise AssertionError("Generation-disabled evaluation unexpectedly produced an answer.")
                if ask_result.get("sources") and any(k in json.dumps(ask_result) for k in
                        ("passage_id", "source_id", "vector", "score", "hash", "debug")):
                    raise AssertionError("Internal evidence data leaked to Ask response.")

            if len(set(generated_by_level.values())) != 3 or len(set(map(frozenset, citations_by_level.values()))) != 1:
                raise AssertionError("Controlled fallback did not vary by level while retaining shared citations.")
            if all(tag_language == language for tag_language, (language, _) in zip(card_languages, scenarios)):
                raise AssertionError("Selected physical cards did not allow a profile-vs-tag-language check.")
            resolved = client.post("/rfid/resolve", headers=device_headers, json={"rfid_uid": uids[0]})
            if resolved.status_code != 200 or resolved.json().get("language") != "ar" or resolved.json().get("level") != "beginner":
                raise AssertionError("RFID resolution did not use the app.visitors profile.")
            conflict = client.post("/rfid/assign", headers=admin_headers,
                                   json={"rfid_uid": uids[0], "card_id": own_visitors[1]})
            if conflict.status_code != 409:
                raise AssertionError("An assigned RFID card was not protected from reassignment.")
            unknown = client.post("/rfid/resolve", headers=device_headers, json={"rfid_uid": "F0F0F0F0"})
            if unknown.status_code != 404:
                raise AssertionError("Unknown RFID card was not rejected safely.")
            with psycopg.connect(dsn) as conn:
                conn.execute("""insert into app.visitors(card_id,lang,level,consent,created_at,expires_at)
                    values(%s,'en','beginner',false,now(),%s)""",
                    (nonconsent_visitor, datetime.now(timezone.utc) + timedelta(hours=1)))
                conn.commit()
            denied = client.post("/rfid/assign", headers=admin_headers,
                                 json={"rfid_uid": uids[0], "card_id": nonconsent_visitor})
            if denied.status_code != 403:
                raise AssertionError("RFID assignment did not reject a visitor without consent.")
            for path in (f"/visitor/{nonconsent_visitor}", f"/visitor/{nonconsent_visitor}/report",
                         f"/visitors/{nonconsent_visitor}/summary"):
                if client.get(path).status_code != 403:
                    raise AssertionError("A history-bearing profile endpoint did not enforce consent.")
            if client.post("/ai/recommend-next-station", json={"card_id": nonconsent_visitor}).status_code != 403:
                raise AssertionError("Recommendation endpoint did not enforce consent.")

            # Deterministic governance branch must intercept before generation.
            fatwa = client.post("/ask", json={"card_id": own_visitors[0],
                "question": "هل يجوز لي ذلك في حالتي الشخصية؟"})
            if fatwa.status_code != 200 or fatwa.json().get("status") != "referral" or not fatwa.json().get("referral"):
                raise AssertionError("Personal-fatwa question was not deterministically referred.")
            unsupported = client.post("/ask", json={"card_id": own_visitors[0],
                "question": "What is the opening time of the west entrance today?"})
            if unsupported.status_code != 200 or unsupported.json().get("status") != "insufficient_sources":
                raise AssertionError("Unsupported question did not abstain safely.")
            print("\nPersonal-fatwa safety:", fatwa.json()["status"], "(deterministic referral)")
            print("Unsupported question:", unsupported.json().get("status"))
            print("Live Gemini narrative generation: BLOCKED_BY_PROVIDER_QUOTA; no live request made in this run.")
    finally:
        # Clear mappings first, then restore prior state and remove only our visitors.
        with psycopg.connect(dsn) as conn:
            conn.execute("delete from app.visitors where card_id=%s", (nonconsent_visitor,))
            for row_id, prior_card in assigned:
                conn.execute("""update app.rfid_cards set card_id=%s where id=%s
                    and card_id=any(%s)""", (prior_card, row_id, own_visitors))
            for card_id in own_visitors:
                conn.execute("delete from app.visitors where card_id=%s", (card_id,))
            conn.commit()
        settings.gemini_api_key, settings.openai_api_key = old_llm_key, old_embed_key
        settings.pgvector_enabled = old_pgvector
        settings.admin_api_key = old_admin_key

    with psycopg.connect(dsn) as conn:
        after = {
            "passages": conn.execute("select count(*) from public.passages").fetchone()[0],
            "embeddings": conn.execute("select count(*) from app.embeddings").fetchone()[0],
            "links": conn.execute("select count(*) from app.station_passages").fetchone()[0],
        }
        mappings = conn.execute("select id,card_id from app.rfid_cards where id=any(%s)",
                                ([row_id for row_id, _ in assigned],)).fetchall()
    if after != baseline or [(r[0], r[1]) for r in mappings] != assigned:
        raise AssertionError("Database integrity counts or prior RFID assignments did not restore exactly.")
    print("\nIntegrity preserved:", after)
    print("Temporary visitors/interactions removed; RFID mappings restored.")
    print("Simulated journey command: python -m evaluation.test_visitor_experience")
    root_logger.setLevel(old_log_level)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

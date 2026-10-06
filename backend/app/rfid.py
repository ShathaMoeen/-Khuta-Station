"""Minimal RFID UID resolution and assignment using the existing card registry."""
from __future__ import annotations

import re

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


_UID_SEPARATORS = re.compile(r"[\s:-]+")


def canonical_rfid_uid(value: str) -> str:
    """Normalize common printed UID formats without accepting arbitrary input."""
    uid = _UID_SEPARATORS.sub("", value).upper()
    if not 8 <= len(uid) <= 32 or len(uid) % 2 or not re.fullmatch(r"[0-9A-F]+", uid):
        raise HTTPException(422, "RFID UID must be 4–16 bytes of hexadecimal data.")
    return uid


async def resolve_rfid_visitor(session: AsyncSession, rfid_uid: str) -> dict:
    uid = canonical_rfid_uid(rfid_uid)
    rows = (await session.execute(text("""select r.card_id,v.lang,v.level,v.consent
        from app.rfid_cards r join app.visitors v on v.card_id=r.card_id
        where regexp_replace(upper(r.rfid_uid),'[^0-9A-F]','','g')=:uid
          and r.is_active is true
          and (v.expires_at is null or v.expires_at>now())"""), {"uid": uid})).mappings().all()
    if len(rows) != 1:
        # Fail closed if malformed legacy data contains a normalized UID collision.
        raise HTTPException(404, "RFID card is unknown, inactive, unassigned, or expired.")
    row = rows[0]
    if not row["consent"]:
        raise HTTPException(403, "Visitor consent is required.")
    # Language and level deliberately come from app.visitors, never rfid_cards.language.
    return {"card_id": row["card_id"], "language": row["lang"], "level": row["level"]}


async def assign_rfid_visitor(session: AsyncSession, rfid_uid: str, card_id: str) -> dict:
    uid = canonical_rfid_uid(rfid_uid)
    cards = (await session.execute(text("""select id,card_id,is_active from app.rfid_cards
        where regexp_replace(upper(rfid_uid),'[^0-9A-F]','','g')=:uid for update"""),
        {"uid": uid})).mappings().all()
    if len(cards) != 1:
        raise HTTPException(404, "RFID card is unknown or inactive.")
    card = cards[0]
    if not card["is_active"]:
        raise HTTPException(404, "RFID card is unknown or inactive.")
    visitor = (await session.execute(text("""select card_id,lang,level,consent from app.visitors
        where card_id=:card and (expires_at is null or expires_at>now()) for update"""),
        {"card": card_id})).mappings().first()
    if visitor is None:
        raise HTTPException(404, "Visitor is unknown or expired.")
    if not visitor["consent"]:
        raise HTTPException(403, "Visitor consent is required.")
    if card["card_id"] not in (None, card_id):
        raise HTTPException(409, "RFID card is already assigned.")
    await session.execute(text("update app.rfid_cards set card_id=:card where id=:id"),
                          {"card": card_id, "id": card["id"]})
    await session.commit()
    return {"assigned": True, "language": visitor["lang"], "level": visitor["level"]}

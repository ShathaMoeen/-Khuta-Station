"""One shared station-tap flow for the demo client and future RFID readers."""
from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AIProviderError, VisitorNotFoundError
from app.rag import RAGService
from app.schemas import GeneratedAnswer, SourceCitation, visitor_citation
from app.services import CrowdingAnalyzer, RecommendationEngine, VisitorAnalyzerService

SUPPORTED_LANGUAGES={'ar','en','fr','tr','id','ur','ru','bn','zh'}
SUPPORTED_LEVELS={'beginner','intermediate','advanced'}


async def register_visitor(session: AsyncSession, lang: str, level: str, consent: bool, card_id: str | None=None) -> dict:
    if not consent:
        raise HTTPException(400, 'Consent is required to create a visitor session.')
    if lang not in SUPPORTED_LANGUAGES or level not in SUPPORTED_LEVELS:
        raise HTTPException(400, 'Unsupported language or visitor level.')
    settings=get_settings()
    if settings.app_env.lower()=='production' and not consent:
        raise HTTPException(400, 'Consent is required to create a visitor session.')
    if card_id and not all(ch.isalnum() or ch in '-_:' for ch in card_id):
        raise HTTPException(400,'Card IDs may contain letters, digits, colon, underscore or hyphen only.')
    card_id=card_id or ('KH-'+secrets.token_hex(6).upper())
    expires=datetime.now(timezone.utc)+timedelta(hours=12)
    try:
        await session.execute(text('''insert into app.visitors(card_id,lang,level,consent,created_at,expires_at)
            values(:card,:lang,:level,true,now(),:expires)'''),
            {'card':card_id,'lang':lang,'level':level,'expires':expires})
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409,'Card ID is already registered.')
    await session.commit()
    return {'card_id':card_id,'expires_at':expires}


async def _station(session: AsyncSession, station_code: str | None=None, station_id: int | None=None) -> dict:
    if station_code:
        row=(await session.execute(text('select id,code,name,topic,location from app.stations where code=:code'),{'code':station_code})).mappings().first()
    else:
        row=(await session.execute(text('select id,code,name,topic,location from app.stations where id=:id'),{'id':station_id})).mappings().first()
    if not row:
        raise HTTPException(404,'Unknown station.')
    return dict(row)


async def _profile(session: AsyncSession, card_id: str) -> dict:
    rows=(await session.execute(text('''select lang,level,consent from app.visitors
        where card_id=:card and (expires_at is null or expires_at>now())'''),{'card':card_id})).mappings().first()
    if not rows:
        raise VisitorNotFoundError('Unknown or expired visitor card')
    if not rows['consent']:
        raise HTTPException(403,'Visitor consent is required.')
    return await VisitorAnalyzerService().analyze(session,card_id)


async def _curated_content(session: AsyncSession, station_id: int, language: str, level: str) -> dict | None:
    rows=(await session.execute(text('''select id,station_id,title,body,source_note,lang,level
        from app.station_content where station_id=:station and lang=:lang and level=:level
        limit 1'''),{'station':station_id,'lang':language,'level':level})).mappings().first()
    return dict(rows) if rows else None


async def _station_evidence(session: AsyncSession, station_id: int) -> list[dict]:
    rows=(await session.execute(text('''select p.id,p.type,p.lang as language,p.source,p.reference,p.url,p.text,
            p.surah,p.ayah,p.authenticity,p.grade,p.attribution,sp.priority,
            cs.id as source_id,cs.rights_status,cs.verification_status,cs.governance_level
        from app.station_passages sp join public.passages p on p.id=sp.passage_id
        left join app.content_sources cs on cs.source_name=p.source and cs.source_type=p.type
        where sp.station_id=:station and sp.relationship_type='supports'
          and (p.type<>'quran' or (cs.id=30 and cs.source_name='مصحف حفص'))
          and (p.type<>'hadith' or (cs.id=2 and p.source='quranlab/hadith:bukhari-ar' and p.reference ~ '(^|[^0-9])(3|5807)$'))
        order by sp.priority desc nulls last,p.type,p.reference limit 12'''),{'station':station_id})).mappings().all()
    return [dict(row) for row in rows]


async def _content_evidence(session: AsyncSession, content_id: int) -> list[dict]:
    """Load and validate the exact evidence mapped to the selected Master Content row."""
    rows=(await session.execute(text('''select p.id,p.type,p.lang as language,p.source,p.reference,p.url,p.text,
            p.surah,p.ayah,p.authenticity,p.grade,p.attribution,cs.id as source_id,
            cs.rights_status,cs.verification_status,cs.governance_level,cs.source_name,cs.source_type,
            pv.id as provenance_id,pv.station_content_id as provenance_content_id,
            pv.passage_id as provenance_passage_id,pv.reference as provenance_reference,
            pv.source_id as provenance_source_id
        from app.station_content_provenance pv
        left join public.passages p on p.id=pv.passage_id
        left join app.content_sources cs on cs.id=pv.source_id
        where pv.station_content_id=:content_id
        order by pv.reference,p.id'''),{'content_id':content_id})).mappings().all()
    result=[dict(row) for row in rows]
    if not result or any(not row.get('text') or not _provenance_reference_matches(row)
                         or row.get('provenance_content_id')!=content_id
                         or str(row.get('provenance_passage_id'))!=str(row.get('id'))
                         or row.get('source_id')!=row.get('provenance_source_id')
                         or row.get('source')!=row.get('source_name')
                         or row.get('type')!=row.get('source_type') for row in result):
        raise AIProviderError('Selected Master Content provenance failed validation')
    return result


def _provenance_reference_matches(row: dict) -> bool:
    """Accept only explicit format variants for known Quran/Hadith references."""
    actual=str(row.get('reference') or '').strip()
    mapped=str(row.get('provenance_reference') or '').strip()
    if actual==mapped:
        return True
    if row.get('type')=='quran':
        quran_match=re.fullmatch(r'(?:Quran\s+)?(\d+):(\d+)',mapped,re.IGNORECASE)
        return bool(quran_match and (int(quran_match.group(1)),int(quran_match.group(2))) ==
                    (row.get('surah'),row.get('ayah')) and actual==f"{row.get('surah')}:{row.get('ayah')}")
    if row.get('type')=='hadith' and row.get('source')=='quranlab/hadith:bukhari-ar':
        actual_number=re.search(r'(?:bukhari:|\b)(\d+)\s*$',actual,re.IGNORECASE)
        mapped_number=re.search(r'(?:bukhari\s*)?(\d+)\s*$',mapped,re.IGNORECASE)
        return bool(actual_number and mapped_number and actual_number.group(1)==mapped_number.group(1)
                    and 'bukhari' in actual.lower() and 'bukhari' in mapped.lower())
    return False


async def _approved_translations(session: AsyncSession, evidence: list[dict], language: str) -> tuple[list[dict], str]:
    quran=[p for p in evidence if p.get('type')=='quran' and p.get('surah') is not None and p.get('ayah') is not None]
    if language=='ar' or not quran:
        return [],'not_applicable'
    translations=[]
    for verse in quran:
        rows=(await session.execute(text('''select p.id,p.type,p.lang as language,p.source,p.reference,p.url,p.text,
                p.surah,p.ayah,p.attribution,cs.rights_status,cs.verification_status,cs.governance_level
            from public.passages p join app.content_sources cs on cs.source_name=p.source and cs.source_type=p.type
            where p.type='quran_translation' and p.lang=:lang and p.surah=:surah and p.ayah=:ayah
              and cs.verification_status='verified' and cs.rights_status='permitted'
              and cs.governance_level='APPROVED_LEVEL_2' limit 2'''),
            {'lang':language,'surah':verse['surah'],'ayah':verse['ayah']})).mappings().all()
        if len(rows)==1:
            translations.append(dict(rows[0]))
        elif len(rows)>1:
            return [],'ambiguous_approved_translation'
    if translations:
        return translations,'available'
    return [],'withheld_source_not_approved'


async def _media(session: AsyncSession, station_id: int, lang: str) -> list[dict]:
    rows=(await session.execute(text('''select id,media_type,title_ar,title_en,caption_ar,caption_en,
            asset_url,thumbnail_url,source_url,institution,creator,license,license_url,attribution_text,
            alt_text_ar,alt_text_en from app.media_assets
        where station_id=:station and verification_status='verified' and rights_status='permitted'
        order by id'''),{'station':station_id})).mappings().all()
    return [dict(row) for row in rows]


def _source_citations(rows: list[dict]) -> list[dict]:
    return [SourceCitation(title=row.get('source') or row.get('type') or 'Source',source=row.get('source') or '',
        reference=row.get('reference'),url=row.get('url'),passage_id=str(row.get('id')),
        content_type=row.get('type'),text=row.get('text'),surah=row.get('surah'),ayah=row.get('ayah'),
        authenticity=row.get('authenticity'),grade=row.get('grade'),attribution=row.get('attribution'),
        rights_status=row.get('rights_status'),verification_status=row.get('verification_status'),
        governance_level=row.get('governance_level')).model_dump(mode='json')
        for row in rows]


async def process_station_tap(session: AsyncSession, card_id: str, station_code: str,
                              request_id: str | None=None) -> dict:
    """Validate, personalize, retrieve mapped DB evidence, generate/fallback, then persist one tap."""
    station=await _station(session,station_code=station_code)
    profile=await _profile(session,card_id)
    request_id=request_id or secrets.token_urlsafe(18)
    existing=(await session.execute(text('''select id,card_id,station_id from app.interactions where request_id=:request_id'''),
        {'request_id':request_id})).mappings().first()
    replay=bool(existing)
    if existing and (existing['card_id']!=card_id or existing['station_id']!=station['id']):
        raise HTTPException(409,'Idempotency key was already used for a different card or station.')
    content=await _curated_content(session,station['id'],profile['language'],profile['level'])
    if not content:
        raise HTTPException(404,'No controlled station content is available for this station.')
    try:
        evidence=await _content_evidence(session,int(content['id']))
    except AIProviderError as exc:
        raise HTTPException(503,'Station content provenance failed validation.') from exc
    if existing:
        interaction_id=existing['id']
    else:
        try:
            interaction_id=(await session.execute(text('''insert into app.interactions(card_id,station_id,request_id)
                values(:card,:station,:request_id) returning id'''),
                {'card':card_id,'station':station['id'],'request_id':request_id})).scalar_one()
        except IntegrityError:
            await session.rollback()
            existing=(await session.execute(text('select id,card_id,station_id from app.interactions where request_id=:request_id'),{'request_id':request_id})).mappings().first()
            if not existing or existing['card_id']!=card_id or existing['station_id']!=station['id']:
                raise HTTPException(409,'Station tap request could not be safely replayed.')
            interaction_id=existing['id']; replay=True
    if not replay:
        await session.commit()
    crowding=await CrowdingAnalyzer().station(session,station['id'])
    recommendation=await RecommendationEngine().recommend(session,card_id,station['id'],profile['language'])
    if recommendation:
        recommendation={key:recommendation[key] for key in ('recommended_station','name','topic','reason')
            if key in recommendation}
    media=await _media(session,station['id'],profile['language'])
    # Visitor citations are loaded only from the selected content's exact,
    # validated provenance. Normal station opening does not call an AI provider.
    citation_rows=evidence
    citations=[visitor_citation(SourceCitation(title=row.get('source') or row.get('type') or 'Source',
        source=row.get('source') or '',reference=row.get('reference'),url=row.get('url'),passage_id=str(row.get('id')),
        content_type=row.get('type'),text=row.get('text'),surah=row.get('surah'),ayah=row.get('ayah'),
        authenticity=row.get('authenticity'),grade=row.get('grade'),attribution=row.get('attribution')))
        for row in citation_rows]
    legacy_content={k:content.get(k) for k in ('title','body','source_note','lang','level')}
    legacy_content['fallback']=False
    public_station={key:value for key,value in station.items() if key!='id'}
    result={'station':public_station,'visitor':{'language':profile['language'],'level':profile['level'],
            'interests':profile['interests'],'visited_stations':profile['visited_stations']},
        'content':legacy_content,'personalized_explanation':content['body'],
        'explanation_source':'database','ai_generated':False,'ai_status':'database_content',
        'sources':citations,'translation_status':'not_applicable','media':media,'crowding':crowding,'recommended_station':recommendation,
        'presentation_mode':'text'}
    return result

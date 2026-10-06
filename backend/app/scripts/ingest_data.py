"""Register sources and optionally embed existing passages in a bounded pilot.

No command in this script updates public.passages. Vector calls are billable; embeddings
are limited to an explicit station-linked pilot of at most 500 passages.
"""
import argparse
import asyncio
import hashlib
import json
import re

from sqlalchemy import text

from app.ai import get_ai_provider
from app.core.config import get_settings

ATOMIC_TYPES = {'quran', 'quran_translation', 'hadith'}


def _split_units(value: str) -> list[str]:
    """Split deterministically at paragraphs, then sentence boundaries."""
    value = value.replace('\r\n', '\n').replace('\r', '\n').strip()
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', value) if p.strip()]
    units = []
    for paragraph in paragraphs:
        units.extend(s.strip() for s in re.split(r'(?<=[.!?؟۔])\s+', paragraph) if s.strip())
    return units or ([value] if value else [])


def _pack_units(units: list[str], size: int, overlap: int) -> list[str]:
    chunks=[]; current=''
    for unit in units:
        if len(unit) > size:
            if current: chunks.append(current); current=''
            # Stable word-boundary splits avoid cutting a word; pathological single
            # tokens are split at the character bound so output remains finite.
            words=unit.split()
            piece=''
            for word in words:
                candidate=(piece+' '+word).strip()
                if len(candidate)>size and piece:
                    chunks.append(piece); tail=piece[-overlap:] if overlap else ''
                    piece=(tail+' '+word).strip()
                else: piece=candidate
                while len(piece)>size:
                    chunks.append(piece[:size]); piece=piece[max(1,size-overlap):]
            if piece: current=piece
            continue
        candidate=(current+' '+unit).strip()
        if current and len(candidate)>size:
            chunks.append(current)
            tail=current[-overlap:] if overlap else ''
            current=(tail+' '+unit).strip()
        else: current=candidate
    if current: chunks.append(current)
    return chunks


def chunk_text(value: str, size: int = 1200, overlap: int = 150, content_type: str | None = None) -> list[str]:
    """Content-aware deterministic chunking; atomic religious records stay whole."""
    value=value or ''
    if not value.strip(): return []
    kind=(content_type or '').lower()
    if kind in ATOMIC_TYPES:
        return [value]
    value=' '.join(value.split())
    if kind == 'tafsir':
        return _pack_units(_split_units(value),size,overlap)
    # Preserve backwards-compatible sentence-aware splitting for other long text.
    return _pack_units(_split_units(value),size,overlap)


def chunk_passage(row: dict, size: int = 1200, overlap: int = 150) -> list[dict]:
    """Return deterministic chunks with the mandatory source identity metadata."""
    kind=row.get('type') or row.get('content_type') or ''
    value=row.get('text') or ''
    parts=chunk_text(value,size,overlap,kind)
    unusually_long_hadith=kind.lower()=='hadith' and len(' '.join(value.split()))>size
    return [{
        'passage_id': row.get('id') or row.get('passage_id'),
        'source': row.get('source'), 'reference': row.get('reference'),
        'language': row.get('lang') or row.get('language'), 'content_type': kind,
        'visitor_level': row.get('level') or row.get('visitor_level'),
        'chunk_index': i, 'chunk_text': part,
        'review_required': unusually_long_hadith,
        'review_reason': 'unusually_long_hadith' if unusually_long_hadith else None,
    } for i,part in enumerate(parts)]


async def run(embed: bool, limit: int | None, batch_size: int, demo_stations: bool):
    from app.db.session import SessionFactory
    settings=get_settings()
    async with SessionFactory() as session:
        async with session.begin():
            sources=(await session.execute(text("select distinct source,type,max(attribution) attribution,max(url) url from public.passages group by source,type order by source,type"))).mappings().all()
            for src in sources:
                key=hashlib.sha256(f"{src['source']}|{src['type']}".encode()).hexdigest()
                metadata={'source':src['source'],'content_type':src['type'],'attribution':src['attribution'],'url':src['url']}
                match=re.search(r'(?i)\bversion\s+([0-9]{4}-[0-9]{2}-[0-9]{2})',src['attribution'] or '')
                source_version=match.group(1) if match else None
                await session.execute(text("""insert into app.content_sources(source_key,source_name,source_type,attribution,attribution_text,source_url,source_version,metadata)
                    values(:key,:name,:type,:attribution,:attribution,:url,:version,cast(:metadata as jsonb))
                    on conflict(source_key) do update set attribution=excluded.attribution,attribution_text=excluded.attribution_text,source_url=excluded.source_url,source_version=coalesce(excluded.source_version,app.content_sources.source_version),metadata=excluded.metadata"""),
                    {'key':key,'name':src['source'],'type':src['type'],'attribution':src['attribution'],'url':src['url'],'version':source_version,'metadata':json.dumps(metadata,ensure_ascii=False)})
        await session.commit()
        if not embed:
            print(f'Registered {len(sources)} source/type pairs. Existing passage rows were read only; embeddings were not created.')
            return
        if not demo_stations or limit is None or limit < 1 or limit > 500:
            raise SystemExit('Embedding is restricted to --demo-stations and an explicit --limit between 1 and 500; full-corpus embedding is disabled.')
        if not settings.ai_provider_configured:
            raise SystemExit('Embedding pilot blocked: configured provider credentials are unavailable; no provider request was made.')
        if settings.embedding_dimensions != 1536:
            raise SystemExit('Embedding pilot blocked: database vector dimension is 1536.')
        indexed=(await session.execute(text('select count(distinct p.id) from public.passages p join app.station_passages sp on sp.passage_id=p.id where not exists(select 1 from app.embeddings e where e.content_id=p.id)'))).scalar_one()
        candidate_ids=(await session.execute(text("""select distinct p.id from public.passages p join app.station_passages sp on sp.passage_id=p.id
            where not exists(select 1 from app.embeddings e where e.content_id=p.id) order by p.id limit :lim"""),{'lim':limit})).scalars().all()
        rows=(await session.execute(text("""select p.id,p.source,p.type,p.lang,p.level,p.text,p.reference,p.url,p.attribution,p.meta
            from public.passages p where p.id=any(:ids) order by p.id"""),{'ids':candidate_ids})).mappings().all()
        estimate=sum(len(chunk_passage(dict(row))) for row in rows)
        print(json.dumps({'pilot_passage_candidates':indexed,'selected_passages':len(rows),'estimated_chunks':estimate,'embedding_model':settings.embedding_model,'configured_dimensions':settings.embedding_dimensions,'database_dimensions':1536,'station_codes':['QURAN-01','WAHY-01','HIJRAH-01','BADR-01','HADITH-01']},ensure_ascii=False))
        provider=get_ai_provider(); processed=0
        while processed<len(rows):
            batch=rows[processed:processed+batch_size]
            await session.rollback()
            chunks=[]; texts=[]
            for row in batch:
                for part in chunk_passage(dict(row)):
                    chunks.append((row,part)); texts.append(part['chunk_text'])
            vectors=[]
            for offset in range(0,len(texts),batch_size): vectors.extend(await provider.embed(texts[offset:offset+batch_size]))
            async with session.begin():
                for (row,part),vector in zip(chunks,vectors):
                    skey=hashlib.sha256(f"{part['source']}|{part['content_type']}".encode()).hexdigest()
                    source_id=(await session.execute(text('select id from app.content_sources where source_key=:key'),{'key':skey})).scalar_one()
                    metadata={'url':row['url'],'attribution':row['attribution'],'record_metadata':row['meta'],'visitor_level':part['visitor_level'],'review_required':part['review_required'],'review_reason':part['review_reason']}
                    await session.execute(text("""insert into app.embeddings(content_id,source_id,chunk_index,language,visitor_level,content_type,chunk_text,reference,metadata,embedding)
                        values(:content,:source,:chunk,:lang,:level,:type,:text,:reference,cast(:metadata as jsonb),cast(:embedding as vector)) on conflict(content_id,chunk_index) do nothing"""),
                        {'content':part['passage_id'],'source':source_id,'chunk':part['chunk_index'],'lang':part['language'],'level':part['visitor_level'],'type':part['content_type'],'text':part['chunk_text'],'reference':part['reference'],'metadata':json.dumps(metadata,ensure_ascii=False),'embedding':'['+','.join(map(str,vector))+']'})
            processed+=len(batch); print(f'Embedded {processed} station-linked passages')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--embed',action='store_true',help='Create vectors only for an explicit station-linked pilot; incurs provider cost.')
    parser.add_argument('--limit',type=int,help='Required pilot cap, maximum 500 passages.')
    parser.add_argument('--batch-size',type=int,default=32)
    parser.add_argument('--demo-stations',action='store_true',help='Restrict embeddings to passages linked to the five controlled demo stations.')
    args=parser.parse_args(); asyncio.run(run(args.embed,args.limit,args.batch_size,args.demo_stations))

if __name__=='__main__': main()

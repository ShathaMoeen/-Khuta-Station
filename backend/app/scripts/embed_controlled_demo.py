"""Create real, idempotent embeddings only for the validated KHUTA demo passages.

This script never updates public.passages, station content, source metadata, or mappings.
It requires an existing DATABASE_URL, a configured compatible embedding provider, and an
exact match to the 19 reviewed station/passage mappings before making provider requests.
"""
from __future__ import annotations

import asyncio
import json
import re

from sqlalchemy import text

from app.ai import get_ai_provider
from app.core.config import get_settings
from app.db.session import SessionFactory
from app.scripts.ingest_data import chunk_passage

STATION_CODES=('BADR-01','HIJRAH-01','QURAN-01','WAHY-01','HADITH-01')
QURAN_COORDS={
    'BADR-01': {(3,123),(3,124),(3,125),(3,126),(3,127)},
    'HIJRAH-01': {(9,40)},
    'QURAN-01': {(96,1),(96,2),(96,3),(96,4),(96,5)},
    'WAHY-01': {(96,1),(96,2),(96,3),(96,4),(96,5)},
    'HADITH-01': set(),
}
HADITH_NUMBERS={'HIJRAH-01':{5807},'WAHY-01':{3},'HADITH-01':{3}}
EXPECTED_LINKS=19
EXPECTED_UNIQUE_PASSAGES=13
EXPECTED_SOURCE_IDS={'quran':30,'hadith':2}
EXPECTED_SOURCE_NAMES={'quran':'مصحف حفص','hadith':'quranlab/hadith:bukhari-ar'}


def _hadith_number(reference: str | None) -> int | None:
    match=re.search(r'(\d+)\s*$',reference or '')
    return int(match.group(1)) if match else None


async def _preflight(session):
    settings=get_settings()
    if not settings.database_url or SessionFactory is None:
        raise SystemExit('Embedding pilot blocked: DATABASE_URL is not configured in backend/.env.')
    if settings.embedding_provider not in {'openai','gemini'} or not settings.ai_provider_configured:
        raise SystemExit('Embedding pilot blocked: configure matching provider names and provider API key in backend/.env.')
    if settings.embedding_dimensions!=1536:
        raise SystemExit('Embedding pilot blocked: existing app.embeddings dimension is vector(1536).')
    passages_before=(await session.execute(text('select count(*) from public.passages'))).scalar_one()
    if passages_before!=166774:
        raise SystemExit(f'Embedding pilot blocked: public.passages count is {passages_before}, expected 166774.')
    vector_type=(await session.execute(text("""select format_type(a.atttypid,a.atttypmod)
        from pg_attribute a join pg_class r on r.oid=a.attrelid join pg_namespace n on n.oid=r.relnamespace
        where n.nspname='app' and r.relname='embeddings' and a.attname='embedding' and not a.attisdropped"""))).scalar_one_or_none()
    if vector_type!='vector(1536)':
        raise SystemExit(f'Embedding pilot blocked: app.embeddings.embedding is {vector_type!r}, expected vector(1536).')

    rows=(await session.execute(text("""select distinct s.code,p.id,p.type,p.source,p.reference,p.surah,p.ayah,
            p.lang,p.level,p.text,p.url,p.attribution,p.meta,cs.id source_id,cs.source_name,
            cs.verification_status,cs.rights_status,cs.governance_level
        from app.station_passages sp join app.stations s on s.id=sp.station_id
        join public.passages p on p.id=sp.passage_id
        left join app.content_sources cs on cs.source_name=p.source and cs.source_type=p.type
        where s.code=any(:codes) and sp.relationship_type='supports'
        order by s.code,p.reference,p.id"""),{'codes':list(STATION_CODES)})).mappings().all()
    if len(rows)!=EXPECTED_LINKS:
        raise SystemExit(f'Embedding pilot blocked: found {len(rows)} controlled links, expected {EXPECTED_LINKS}.')
    actual_quran={code:set() for code in STATION_CODES}
    actual_hadith={code:set() for code in STATION_CODES}
    unique={}
    for row in rows:
        kind=row['type']; code=row['code']
        if kind not in EXPECTED_SOURCE_IDS or row['source_id']!=EXPECTED_SOURCE_IDS[kind] or row['source_name']!=EXPECTED_SOURCE_NAMES[kind]:
            raise SystemExit(f'Embedding pilot blocked: an unexpected or missing source mapping exists for {code} / {row["reference"]}.')
        if row['governance_level']!='APPROVED_LEVEL_2':
            raise SystemExit(f'Embedding pilot blocked: source is not approved for Level 2: {row["source_name"]!r}.')
        if kind=='quran':
            actual_quran[code].add((row['surah'],row['ayah']))
        elif kind=='hadith':
            if row['source_id']!=2 or row['source_name']!='quranlab/hadith:bukhari-ar':
                raise SystemExit('Embedding pilot blocked: only the separately reviewed Bukhari source is allowed.')
            number=_hadith_number(row['reference'])
            if number is None: raise SystemExit('Embedding pilot blocked: could not parse a controlled Hadith reference.')
            actual_hadith[code].add(number)
        if not row['text']:
            raise SystemExit(f'Embedding pilot blocked: passage {row["id"]} has empty source text.')
        key=str(row['id'])
        if key not in unique:
            unique[key]={**dict(row),'_station_codes':set()}
        unique[key]['_station_codes'].add(code)

    for code in STATION_CODES:
        if actual_quran[code]!=QURAN_COORDS[code] or actual_hadith[code]!=HADITH_NUMBERS.get(code,set()):
            raise SystemExit(f'Embedding pilot blocked: controlled reference set does not match the reviewed list for {code}.')
    if len(unique)!=EXPECTED_UNIQUE_PASSAGES:
        raise SystemExit(f'Embedding pilot blocked: found {len(unique)} unique passage IDs, expected {EXPECTED_UNIQUE_PASSAGES}.')

    passages=list(unique.values())
    existing=(await session.execute(text('''select content_id,chunk_index from app.embeddings
        where content_id=any(:ids)'''),{'ids':[row['id'] for row in passages]})).all()
    existing_keys={(str(r[0]),r[1]) for r in existing}
    total_before=(await session.execute(text('select count(*) from app.embeddings'))).scalar_one()
    return settings,passages,existing_keys,passages_before,total_before


async def run():
    if SessionFactory is None:
        raise SystemExit('Embedding pilot blocked: DATABASE_URL is not configured in backend/.env.')
    async with SessionFactory() as session:
        settings,passages,existing_keys,passages_before,embeddings_before=await _preflight(session)
        await session.rollback()
        pending=[]
        for row in passages:
            for part in chunk_passage(row):
                if (str(row['id']),part['chunk_index']) not in existing_keys:
                    pending.append((row,part))
        print(json.dumps({'passages_before':passages_before,'embeddings_before':embeddings_before,
            'unique_controlled_passages':len(passages),'existing_pilot_chunks':len(existing_keys),
            'new_chunks_to_embed':len(pending),'embedding_provider':settings.embedding_provider,
            'embedding_model':settings.embedding_model,'database_dimension':1536,
            'actual_output_dimension':'NOT_MEASURED'},ensure_ascii=False))
        if not pending:
            after=(await session.execute(text('select count(*) from app.embeddings'))).scalar_one()
            print(json.dumps({'embeddings_after':after,'new_rows':0,
                'runtime_dimension_probe':'NOT_RUN_NO_PENDING_EMBEDDINGS'},ensure_ascii=False))
            return

        provider=get_ai_provider()
        output_dimension=await provider.probe_embedding('KHUTA controlled-pilot dimension verification.')
        print(json.dumps({'provider':settings.embedding_provider,'embedding_model':settings.embedding_model,
            'actual_output_dimension':output_dimension,'database_dimension':1536},ensure_ascii=False))
        if output_dimension!=1536:
            raise SystemExit('Embedding pilot stopped before controlled embedding batch: actual provider output is not vector(1536).')
        vectors=await provider.embed([part['chunk_text'] for _,part in pending])
        dimensions={len(vector) for vector in vectors}
        if len(vectors)!=len(pending) or dimensions!={1536}:
            raise SystemExit(f'Embedding pilot stopped before insert: provider returned dimensions {sorted(dimensions)}.')

        async with session.begin():
            for (row,part),vector in zip(pending,vectors):
                source_id=row['source_id']
                if source_id is None:
                    raise SystemExit(f'Embedding pilot stopped: no source registry row for passage {row["id"]}.')
                metadata={'url':row['url'],'attribution':row['attribution'],'record_metadata':row['meta'],
                    'visitor_level':part['visitor_level'],'review_required':part['review_required'],
                    'review_reason':part['review_reason'],'station_codes':sorted(row['_station_codes']),
                    'verification_status':row['verification_status'],'rights_status':row['rights_status'],
                    'governance_level':row['governance_level']}
                await session.execute(text("""insert into app.embeddings(content_id,source_id,chunk_index,language,
                    visitor_level,content_type,chunk_text,reference,metadata,embedding)
                    values(:content,:source,:chunk,:lang,:level,:type,:text,:reference,cast(:metadata as jsonb),cast(:embedding as vector))
                    on conflict(content_id,chunk_index) do nothing"""),{
                    'content':row['id'],'source':source_id,'chunk':part['chunk_index'],'lang':part['lang'] if 'lang' in part else part['language'],
                    'level':part['visitor_level'],'type':part['content_type'],'text':part['chunk_text'],'reference':part['reference'],
                    'metadata':json.dumps(metadata,ensure_ascii=False),'embedding':'['+','.join(map(str,vector))+']'})
        passage_ids=[row['id'] for row in passages]
        stored=(await session.execute(text('''select e.content_id,e.source_id,e.chunk_index,e.language,
                e.content_type,e.chunk_text,e.reference,vector_dims(e.embedding) dimensions,
                p.source,p.type,p.lang,p.text,p.reference passage_reference
            from app.embeddings e join public.passages p on p.id=e.content_id
            where e.content_id=any(:ids) order by e.content_id,e.chunk_index'''),{'ids':passage_ids})).mappings().all()
        expected={}
        for row in passages:
            for part in chunk_passage(row):
                expected[(str(row['id']),part['chunk_index'])]=(row,part)
        duplicate_keys=(await session.execute(text('''select count(*) from (
            select content_id,chunk_index from app.embeddings group by content_id,chunk_index having count(*)>1
        ) duplicates'''))).scalar_one()
        validation_errors=[]
        if len(stored)!=len(expected):
            validation_errors.append(f'expected {len(expected)} pilot chunks, found {len(stored)}')
        for item in stored:
            key=(str(item['content_id']),item['chunk_index'])
            pair=expected.get(key)
            if pair is None:
                validation_errors.append(f'unexpected controlled chunk {key}')
                continue
            row,part=pair
            expected_lang=part['lang'] if 'lang' in part else part['language']
            if (item['dimensions']!=1536 or item['source_id']!=row['source_id']
                or item['reference']!=part['reference'] or item['passage_reference']!=row['reference']
                or item['chunk_text']!=part['chunk_text'] or item['source']!=row['source']
                or item['content_type']!=row['type'] or item['type']!=row['type']
                or item['language']!=expected_lang or item['lang']!=expected_lang):
                validation_errors.append(f'mapping, dimension, reference, language, or exact source text mismatch for {key}')
        after=(await session.execute(text('select count(*) from app.embeddings'))).scalar_one()
        passages_after=(await session.execute(text('select count(*) from public.passages'))).scalar_one()
        links_after=(await session.execute(text('''select count(*) from app.station_passages sp join app.stations s on s.id=sp.station_id
            where s.code=any(:codes) and sp.relationship_type='supports' '''),{'codes':list(STATION_CODES)})).scalar_one()
        if duplicate_keys or validation_errors or passages_after!=166774 or links_after!=EXPECTED_LINKS:
            raise SystemExit('Embedding pilot post-insert verification failed: '+('; '.join(validation_errors) or
                f'duplicate_keys={duplicate_keys}, passages={passages_after}, controlled_links={links_after}'))
        validation={'chunks':len(stored),'passages':len({str(item['content_id']) for item in stored}),
            'wrong_dimensions':0,'duplicates':duplicate_keys}
        if validation['passages']!=len(passages):
            raise SystemExit('Embedding pilot verification failed after insert; review the reported counts before continuing.')
        print(json.dumps({'passages_after':passages_before,'embeddings_before':embeddings_before,
            'embeddings_after':after,'unique_passages_embedded':validation['passages'],
            'pilot_chunks':validation['chunks'],'actual_output_dimension':1536,
            'wrong_dimensions':validation['wrong_dimensions'],'duplicate_keys':validation['duplicates'],
            'controlled_links_after':links_after},ensure_ascii=False))


if __name__=='__main__':
    asyncio.run(run())

"""Developer-only retrieval comparison for the fixed 19-link KHUTA demo scope.

Read-only with respect to PostgreSQL. Writes diagnostic results only to this evaluation
directory. It never calls an LLM or changes references, passages, mappings, or vectors.
"""
from __future__ import annotations

import asyncio
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import SessionFactory
from app.rag import RAGService
from app.schemas import QuestionCategory

HERE=Path(__file__).resolve().parent
RESULTS=HERE/'results'/'controlled_retrieval_comparison.json'
QURAN='3:123 3:124 3:125 3:126 3:127'
ALAQ='96:1 96:2 96:3 96:4 96:5'
CASES=[
    {'id':'ar_revelation_begin','language':'ar','station':'WAHY-01','question':'كيف بدأ نزول الوحي؟','expected':[*ALAQ.split(),'bukhari:3']},
    {'id':'ar_badr','language':'ar','station':'BADR-01','question':'ماذا يذكر القرآن عن بدر؟','expected':QURAN.split()},
    {'id':'ar_hijrah','language':'ar','station':'HIJRAH-01','question':'ماذا حدث أثناء الهجرة؟','expected':['9:40','bukhari:5807']},
    {'id':'ar_hira','language':'ar','station':'WAHY-01','question':'ماذا حدث في غار حراء؟','expected':[*ALAQ.split(),'bukhari:3']},
    {'id':'ar_alaq','language':'ar','station':'QURAN-01','question':'ما الذي تقوله سورة العلق عن بداية الوحي؟','expected':ALAQ.split()},
    {'id':'en_revelation_begin','language':'en','station':'WAHY-01','question':'How did revelation begin?','expected':[*ALAQ.split(),'bukhari:3']},
    {'id':'en_badr','language':'en','station':'BADR-01','question':'What does the Quran say about Badr?','expected':QURAN.split()},
    {'id':'en_hijrah','language':'en','station':'HIJRAH-01','question':'What happened during the Hijrah?','expected':['9:40','bukhari:5807']},
    {'id':'en_hira','language':'en','station':'WAHY-01','question':'What happened in the cave of Hira?','expected':[*ALAQ.split(),'bukhari:3']},
    {'id':'en_alaq','language':'en','station':'QURAN-01','question':'What does Surah Al-Alaq say about the beginning of revelation?','expected':ALAQ.split()},
]


def canonical_reference(row:dict)->str:
    if row.get('surah') is not None and row.get('ayah') is not None:
        return f"{row['surah']}:{row['ayah']}"
    if row.get('type')=='hadith' and row.get('source')=='quranlab/hadith:bukhari-ar':
        found=re.search(r'(\d+)\s*$',row.get('reference') or '')
        if found and int(found.group(1)) in {3,5807}:
            return f"bukhari:{found.group(1)}"
    return row.get('reference') or ''


def metric(rows:list[dict],language:str|None=None)->dict:
    selected=[row for row in rows if language is None or row['language']==language]
    ranks=[]
    for row in selected:
        first=next((i for i,ref in enumerate(row['retrieved_references'],1) if ref in row['expected']),None)
        ranks.append(first)
    n=len(ranks)
    return {'queries':n,
        'recall_at_1':sum(r is not None and r<=1 for r in ranks)/n if n else None,
        'recall_at_3':sum(r is not None and r<=3 for r in ranks)/n if n else None,
        'recall_at_5':sum(r is not None and r<=5 for r in ranks)/n if n else None,
        'mrr':sum(1/r if r else 0 for r in ranks)/n if n else None}


async def main():
    settings=get_settings()
    if not settings.database_url or SessionFactory is None:
        raise SystemExit('Retrieval comparison blocked: configure DATABASE_URL in backend/.env first.')
    async with SessionFactory() as session:
        passage_count=(await session.execute(text('select count(*) from public.passages'))).scalar_one()
        embedding_count=(await session.execute(text('select count(*) from app.embeddings'))).scalar_one()
        vector_type=(await session.execute(text("""select format_type(a.atttypid,a.atttypmod)
            from pg_attribute a join pg_class r on r.oid=a.attrelid join pg_namespace n on n.oid=r.relnamespace
            where n.nspname='app' and r.relname='embeddings' and a.attname='embedding' and not a.attisdropped"""))).scalar_one_or_none()
        stored_dim=(await session.execute(text('select max(vector_dims(embedding)) from app.embeddings'))).scalar_one_or_none()
        if passage_count!=166774: raise SystemExit(f'Expected 166774 public passages; found {passage_count}.')
        if vector_type!='vector(1536)': raise SystemExit(f'Expected app.embeddings.embedding vector(1536); found {vector_type!r}.')
        if settings.embedding_dimensions!=1536: raise SystemExit('Configured embedding dimensions differ from the existing vector(1536) schema.')
        if embedding_count and not settings.ai_provider_configured:
            raise SystemExit('Vector retrieval comparison blocked: existing vectors require a configured query-embedding provider key.')
        station_ids=dict((await session.execute(text('select code,id from app.stations where code=any(:codes)'),
            {'codes':sorted({case['station'] for case in CASES})})).all())
        if set(station_ids)!={case['station'] for case in CASES}:
            raise SystemExit('Controlled retrieval comparison blocked: one or more expected station codes are missing.')
        rag=RAGService(); records=[]; by_method={mode:[] for mode in ('lexical','vector','hybrid')}
        for case in CASES:
            for mode in by_method:
                if mode=='vector' and not embedding_count:
                    found=[]; mode_status='no_vectors'
                else:
                    found=await rag.retrieve(session,case['question'],case['language'],QuestionCategory.islamic_knowledge,
                        'beginner',limit=5,station_id=station_ids[case['station']],retrieval_mode=mode)
                    mode_status='measured'
                ranked=[{'rank':i,'passage_id':str(p['id']),'type':p.get('type'),'reference':p.get('reference'),
                    'canonical_reference':canonical_reference(p),'source':p.get('source'),'score':p.get('score'),
                    'text_preview':(p.get('text') or '')[:180]} for i,p in enumerate(found,1)]
                result={'case_id':case['id'],'question':case['question'],'language':case['language'],
                    'station_code':case['station'],'expected':case['expected'],'retrieved_references':[x['canonical_reference'] for x in ranked],
                    'ranked':ranked,'status':mode_status}
                by_method[mode].append(result)
        summary={mode:{'status':('NOT_MEASURED_NO_VECTORS' if mode=='vector' and not embedding_count else
                ('lexical_fallback_no_vectors' if mode=='hybrid' and not embedding_count else 'measured')),
            'overall':metric(rows),'arabic':metric(rows,'ar'),'english':metric(rows,'en')}
            for mode,rows in by_method.items()}
        measured=['lexical']+(['vector','hybrid'] if embedding_count else [])
        selected=max(measured,key=lambda mode:(summary[mode]['overall']['recall_at_5'],
            summary[mode]['overall']['mrr'],summary[mode]['overall']['recall_at_3'],
            summary[mode]['overall']['recall_at_1'],-measured.index(mode)))
        report={'created_at':datetime.now(timezone.utc).isoformat(),'evaluation_type':'fixed controlled-station retrieval; developer diagnostics',
            'passage_count':passage_count,'embeddings_before':embedding_count,'vector_type':vector_type,
            'stored_vector_dimension':stored_dim if stored_dim is not None else 'NOT_MEASURED_NO_VECTORS',
            'embedding_provider':settings.embedding_provider,'embedding_model':settings.embedding_model,
            'configured_embedding_dimension':settings.embedding_dimensions,'actual_provider_output_dimension':stored_dim if stored_dim is not None else 'NOT_MEASURED',
            'methods':summary,'cases':by_method,
            'selected_strategy':selected if embedding_count else 'lexical (only measured method); vector retrieval NOT_MEASURED_NO_VECTORS'}
        RESULTS.parent.mkdir(parents=True,exist_ok=True)
        RESULTS.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'passage_count':passage_count,'embeddings':embedding_count,'vector_type':vector_type,
            'provider':settings.embedding_provider,'model':settings.embedding_model,'methods':summary,
            'results_file':str(RESULTS)},ensure_ascii=False,indent=2))


if __name__=='__main__': asyncio.run(main())

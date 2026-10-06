from typing import Protocol
import unicodedata
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import get_ai_provider
from app.core.config import get_settings


def normalize_search_text(value: str) -> str:
    """Normalize common Arabic orthographic variants and punctuation for search only."""
    digits=str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹','01234567890123456789')
    value=value.translate(digits)
    value=''.join(ch for ch in value if not unicodedata.combining(ch) and not ('\u064b' <= ch <= '\u065f') and ch!='\u0670')
    value=value.translate(str.maketrans({'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ي','ـ':None,'،':' ','؛':' ','؟':' ','ـ':' '}))
    return re.sub(r'\s+', ' ', value).strip()


def exact_reference(question: str) -> tuple[str, ...] | tuple[int, int] | None:
    """Recognize explicit Quran coordinates and common collection/number references."""
    q=normalize_search_text(question)
    quran=re.search(r'(?<!\d)(\d{1,3})\s*:\s*(\d{1,3})(?!\d)',q)
    if quran:
        return int(quran.group(1)),int(quran.group(2))
    hadith=re.search(r'\b(?:sahih\s+al\s+)?(bukhari|muslim|abu\s+dawud|abudawud|ibn\s+majah|ibnmajah|nasai|tirmidhi|malik)\s*(?:#|:)?\s*(\d+)\b',q,re.I)
    if hadith:
        collection=hadith.group(1).lower().replace(' ','')
        alias={'bukhari':'bukhari','muslim':'muslim','abudawud':'abudawud','ibnmajah':'ibnmajah','nasai':'nasai','tirmidhi':'tirmidhi','malik':'malik'}[collection]
        return (alias,hadith.group(2))
    colon=re.search(r'\b(bukhari|muslim|abudawud|ibnmajah|nasai|tirmidhi|malik)\s*:\s*(\d+)\b',q,re.I)
    if colon:
        return (colon.group(1).lower(),colon.group(2))
    return None


class ContentSource(Protocol):
    async def search(self, session: AsyncSession, question: str, language: str, level: str, limit: int, station_id: int | None = None, topic: str | None = None, retrieval_mode: str = 'hybrid') -> list[dict]: ...


def _fuse_rrf(vector_rows: list[dict], lexical_rows: list[dict], limit: int) -> list[dict]:
    """Reciprocal-rank fusion keeps vector and lexical evidence complementary."""
    merged={}
    for ranked in (vector_rows,lexical_rows):
        for rank,row in enumerate(ranked,1):
            key=str(row['id'])
            if key not in merged: merged[key]={**row,'score':0.0,'retrieval_channels':[]}
            else:
                for field,value in row.items():
                    if merged[key].get(field) is None and value is not None:
                        merged[key][field]=value
            merged[key]['score'] += 1/(60+rank)
            merged[key]['retrieval_channels'].append('vector' if ranked is vector_rows else 'lexical')
            if len(row.get('text',''))>len(merged[key].get('text','')): merged[key]['text']=row['text']
    return sorted(merged.values(),key=lambda x:x['score'],reverse=True)[:limit]


class ExhibitionContentSource:
    async def search(self, session: AsyncSession, question: str, language: str, level: str, limit: int, station_id: int | None = None, topic: str | None = None, retrieval_mode: str = 'hybrid') -> list[dict]:
        if retrieval_mode not in {'lexical','vector','hybrid'}: raise ValueError('Unsupported retrieval mode.')
        if retrieval_mode=='vector': return []
        station_filter=' and c.station_id=:station_id' if station_id is not None else ''
        params={'lang':language,'level':level,'query':normalize_search_text(question),'limit':limit}
        if station_id is not None: params['station_id']=station_id
        params['allow_demo_drafts']=get_settings().app_env.lower()=='development'
        rows=(await session.execute(text("""select ('station-' || s.id::text || '-' || c.id::text) as id,
            'exhibition' as type,c.lang,s.name as source,c.title as reference,null::text as url,c.body as text,
            ts_rank(to_tsvector('simple',c.body),replace(plainto_tsquery('simple',:query)::text,' & ',' | ')::tsquery) as score
            from app.station_content c join app.stations s on s.id=c.station_id
            where c.lang=:lang and c.level in (:level,'beginner') {station_filter}
            and coalesce(lower(c.source_note),'') not like '%sample%'
            and coalesce(c.source_note,'') not like '%تجريبي%'
            and coalesce(lower(c.title),'') not like 'sample%'
            and coalesce(lower(c.body),'') not like '%to be replaced with%'
            and (:allow_demo_drafts or (exists(select 1 from app.station_content_provenance pv where pv.station_content_id=c.id) and not exists(select 1 from app.station_content_provenance pv where pv.station_content_id=c.id and (pv.verification_status<>'verified' or pv.rights_status<>'permitted'))))
            and to_tsvector('simple',c.body) @@ replace(plainto_tsquery('simple',:query)::text,' & ',' | ')::tsquery
            order by (c.level=:level) desc,score desc limit :limit""".format(station_filter=station_filter)),params)).mappings().all()
        return [{'id':str(r['id']),'type':r['type'],'language':r['lang'],'source':r['source'],'reference':r['reference'],'url':r['url'],'text':r['text'],'score':float(r['score'] or 0),'retrieval_channels':['lexical']} for r in rows]


class PassageContentSource:
    async def search(self, session: AsyncSession, question: str, language: str, level: str, limit: int, station_id: int | None, topic: str | None, types: list[str], approved_sources: list[str], retrieval_mode: str = 'hybrid') -> list[dict]:
        if retrieval_mode not in {'lexical','vector','hybrid'}: raise ValueError('Unsupported retrieval mode.')
        search_question=question+(f' {topic}' if topic else '')
        query=normalize_search_text(search_question)
        excerpt=normalize_search_text(question.split(':',1)[-1]).strip().lower()
        excerpt_words=excerpt.split()
        # Evaluation and exhibit questions may end on a truncated final word. Use
        # the complete leading phrase to boost an exact stored passage safely.
        phrase=' '.join(excerpt_words[:-1]) if len(excerpt_words)>1 else ''
        settings=get_settings()
        source_filter=' and source = any(:approved)' if approved_sources else ''
        if 'fatwa' in types and not approved_sources: return []
        params={'lang':language,'types':types,'level':level,'query':query,'topic':normalize_search_text(topic or ''),'phrase':phrase,'limit':max(limit*4,limit)}
        if source_filter: params['approved']=approved_sources
        station_join="left join app.station_passages sp on sp.passage_id=p.id and sp.station_id=:station_id and sp.relationship_type='supports'" if station_id is not None else 'left join app.station_passages sp on false'
        if station_id is not None: params['station_id']=station_id
        language_filter="(p.lang=:lang or (sp.station_id is not null and p.lang='ar'))" if station_id is not None else 'p.lang=:lang'
        governance_filter=('and sp.station_id is not null' if station_id is not None else
            "and cs.verification_status='verified' and cs.rights_status='permitted' and cs.governance_level in ('APPROVED_LEVEL_1','APPROVED_LEVEL_2')")
        quran_source_scope="and (p.type<>'quran' or (cs.id=30 and cs.source_name='مصحف حفص'))"
        hadith_allowlist="and (p.type<>'hadith' or (cs.id=2 and p.source='quranlab/hadith:bukhari-ar' and p.reference ~ '(^|[^0-9])(3|5807)$'))"
        recognized=exact_reference(question)
        exact_clause='false'
        if isinstance(recognized,tuple) and len(recognized)==2 and isinstance(recognized[0],int):
            params['ref_surah'],params['ref_ayah']=recognized
            exact_clause='(p.surah=:ref_surah and p.ayah=:ref_ayah)'
        elif isinstance(recognized,tuple) and len(recognized)==2:
            collection,number=recognized
            params['exact_reference']=f'{collection}:{number}'
            exact_clause='p.reference=:exact_reference'
        tokens=[w for w in re.findall(r'[^\W_]{2,}',query,re.UNICODE) if len(w)>1][:12]
        params['fallback_terms']=[f'%{w}%' for w in tokens]
        lexical=(await session.execute(text(f"""with q as (
            select replace(plainto_tsquery('simple',:query)::text,' & ',' | ')::tsquery query_ts,
                   replace(plainto_tsquery('simple',:topic)::text,' & ',' | ')::tsquery topic_ts
        )
        select p.id,p.type,p.lang,p.source,p.reference,p.url,p.text,p.surah,p.ayah,p.authenticity,p.grade,p.attribution,
          cs.id as source_id,
          cs.rights_status,cs.verification_status,cs.governance_level,
          ts_rank(to_tsvector('simple',p.text_norm),q.query_ts || q.topic_ts)
          + case when length(:phrase)>12 and strpos(lower(p.text_norm),:phrase)>0 then 1.0 else 0.0 end
          + case when {exact_clause} then 10.0 else 0.0 end
          + case when sp.station_id is not null then 2.0*coalesce(sp.priority,1.0) else 0.0 end as score
        from public.passages p cross join q
        left join app.content_sources cs on cs.source_name=p.source and cs.source_type=p.type
        {station_join}
        where p.type=any(:types) and {language_filter} and (p.level is null or p.level='all' or p.level=:level) {source_filter} {governance_filter} {quran_source_scope} {hadith_allowlist}
          and (to_tsvector('simple',p.text_norm) @@ (q.query_ts || q.topic_ts)
               or {exact_clause} or p.text_norm ilike any(:fallback_terms) or sp.station_id is not null)
        order by score desc limit :limit"""),params)).mappings().all()
        lexical_rows=[{'id':str(r['id']),'type':r['type'],'language':r['lang'],'source':r['source'],'source_id':r['source_id'],'reference':r['reference'],'url':r['url'],'text':r['text'],'score':float(r['score'] or 0),'surah':r['surah'],'ayah':r['ayah'],'authenticity':r['authenticity'],'grade':r['grade'],'attribution':r['attribution'],'rights_status':r['rights_status'],'verification_status':r['verification_status'],'governance_level':r['governance_level'],'retrieval_channels':['lexical']} for r in lexical]
        if retrieval_mode=='lexical': return lexical_rows[:limit]
        vector_rows=[]
        if settings.pgvector_enabled and settings.ai_provider_configured and settings.embedding_model:
            indexed_language_filter='e.language=:lang'
            indexed_params={'lang':language,'types':types,'level':level}
            if station_id is not None:
                indexed_language_filter="(e.language=:lang or (e.language='ar' and exists(select 1 from app.station_passages sp where sp.passage_id=e.content_id and sp.station_id=:station_id and sp.relationship_type='supports')))"
                indexed_params['station_id']=station_id
            indexed=(await session.execute(text(f"""select exists(select 1 from app.embeddings e
                where {indexed_language_filter} and e.content_type=any(:types)
                  and (e.visitor_level is null or e.visitor_level='all' or e.visitor_level=:level))"""),indexed_params)).scalar_one()
            if indexed:
                provider=get_ai_provider()
                vector=(await provider.embed_query([search_question]))[0]
                approved_filter=' and cs.source_name = any(:approved)' if approved_sources else ''
                vector_station_join="left join app.station_passages sp on sp.passage_id=p.id and sp.station_id=:station_id and sp.relationship_type='supports'" if station_id is not None else 'left join app.station_passages sp on false'
                vector_language_filter='e.language=:lang' if station_id is None else "(e.language=:lang or (e.language='ar' and sp.station_id is not null))"
                vector_hadith_allowlist="and (e.content_type<>'hadith' or (cs.id=2 and p.source='quranlab/hadith:bukhari-ar' and p.reference ~ '(^|[^0-9])(3|5807)$'))"
                vector_quran_source_scope="and (e.content_type<>'quran' or (cs.id=30 and cs.source_name='مصحف حفص'))"
                vector_governance=('and sp.station_id is not null' if station_id is not None else
                    "and cs.verification_status='verified' and cs.rights_status='permitted' and cs.governance_level in ('APPROVED_LEVEL_1','APPROVED_LEVEL_2')")
                vparams={'lang':language,'types':types,'level':level,'limit':max(limit*4,limit),'vector':'['+','.join(map(str,vector))+']'}
                if station_id is not None: vparams['station_id']=station_id
                if approved_filter: vparams['approved']=approved_sources
                vectors=(await session.execute(text(f"""select e.content_id as id,e.content_type as type,e.language,e.chunk_text as text,e.reference,cs.id as source_id,cs.source_name as source,p.url,
                    p.surah,p.ayah,p.authenticity,p.grade,p.attribution,cs.rights_status,cs.verification_status,cs.governance_level,
                    1-(e.embedding <=> cast(:vector as vector))+case when sp.station_id is not null then 2.0*coalesce(sp.priority,1.0) else 0.0 end as score
                    from app.embeddings e join app.content_sources cs on cs.id=e.source_id
                    join public.passages p on p.id=e.content_id {vector_station_join}
                    where {vector_language_filter} and e.content_type=any(:types) and (e.visitor_level is null or e.visitor_level='all' or e.visitor_level=:level) {approved_filter}
                      {vector_governance} {vector_quran_source_scope} {vector_hadith_allowlist}
                    order by e.embedding <=> cast(:vector as vector) limit :limit"""),vparams)).mappings().all()
                vector_rows=[dict(r) for r in vectors]
        if retrieval_mode=='vector': return vector_rows[:limit]
        if vector_rows: return _fuse_rrf(vector_rows,lexical_rows,limit)
        return lexical_rows[:limit]

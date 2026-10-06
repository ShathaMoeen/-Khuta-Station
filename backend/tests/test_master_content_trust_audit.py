"""Read-only audit for the final 48 visitor-facing station content variants."""
import os

import pytest

from app.core.config import get_settings
from app.station_flow import _provenance_reference_matches

pytestmark=pytest.mark.skipif(os.getenv('KHUTA_DB_AUDIT')!='1' or not get_settings().database_url,
    reason='run explicitly with KHUTA_DB_AUDIT=1 against the existing KHUTA database')

STATIONS=('TAWHEED-01','KAABA-01','SALAH-01','SEERAH-01','HISTORY-01','QURAN-01','WUDU-01','ZAKAT-01')


def _dsn():
    value=get_settings().database_url
    return value.replace('postgresql+asyncpg://','postgresql://',1)


def test_all_48_installed_rows_have_exact_provenance_and_evidence():
    import psycopg

    query='''select s.code station,c.id content_id,c.lang,c.level,c.body,
        pv.id provenance_id,pv.station_content_id,pv.passage_id provenance_passage_id,pv.reference provenance_reference,
        pv.source_id provenance_source_id,pv.verification_status provenance_verification,pv.rights_status provenance_rights,
        p.id passage_id,p.type,p.reference,p.text,p.source,p.lang passage_language,p.surah,p.ayah,
        cs.id source_id,cs.source_name,cs.source_type,cs.verification_status,cs.rights_status,cs.governance_level
        from app.station_content c join app.stations s on s.id=c.station_id
        left join app.station_content_provenance pv on pv.station_content_id=c.id
        left join public.passages p on p.id=pv.passage_id
        left join app.content_sources cs on cs.id=pv.source_id
        where s.code=any(%s) order by s.code,c.lang,c.level,pv.reference'''
    with psycopg.connect(_dsn(),row_factory=psycopg.rows.dict_row) as conn:
        conn.execute('set transaction read only')
        rows=conn.execute(query,(list(STATIONS),)).fetchall()
        counts={}
        for row in rows:
            key=(row['station'],row['lang'],row['level'])
            counts[key]=counts.get(key,0)+1
            assert row['body'] and row['body'].strip()
            assert row['provenance_id'] is not None
            assert row['passage_id']==row['provenance_passage_id']
            assert row['text'] and row['text'].strip()
            assert row['source_id']==row['provenance_source_id']
            assert row['source']==row['source_name']
            assert row['type']==row['source_type']
            assert _provenance_reference_matches({
                'type':row['type'],'source':row['source'],'reference':row['reference'],
                'provenance_reference':row['provenance_reference'],'surah':row['surah'],'ayah':row['ayah']})
            assert row['type'] in {'quran','hadith','tafsir','tafsir_translation','quran_translation','islamic_education'}
        expected={(station,lang,level) for station in STATIONS for lang in ('ar','en')
            for level in ('beginner','intermediate','advanced')}
        assert set(counts)==expected
        assert all(counts[key]>0 for key in expected)
        by_variant={(r['station'],r['lang'],r['level']):r['body'] for r in rows}
        # Historical claims about the first revelation need the mapped Bukhari 3
        # narration; Quran-only versions now describe only what 96:1-5 state.
        for key in (('QURAN-01','ar','beginner'),('QURAN-01','ar','intermediate'),
                    ('QURAN-01','en','beginner'),('QURAN-01','en','intermediate')):
            body=by_variant[key].casefold()
            assert 'بدأ نزول الوحي' not in body
            assert 'began with the first revelation' not in body
            assert 'revealed to the prophet muhammad' not in body
        assert any(term in by_variant[('QURAN-01','ar','advanced')].casefold()
            for term in ('bukhari','البخاري'))
        assert 'bukhari' in by_variant[('QURAN-01','en','advanced')].casefold()
        for lang in ('ar','en'):
            for level in ('beginner','intermediate','advanced'):
                body=by_variant[('WUDU-01',lang,level)].casefold()
                assert 'غسل القدمين' not in body
                assert 'washing the feet' not in body
        assert conn.execute('select count(*) from public.passages').fetchone()['count']==166774
        assert conn.execute('select count(*) from app.embeddings').fetchone()['count']==13
        assert conn.execute('select count(*) from app.stations').fetchone()['count']==14
        assert conn.execute('select count(*) from app.station_passages').fetchone()['count']==58
        assert conn.execute('select count(*) from app.station_content').fetchone()['count']==75
        assert conn.execute('select count(*) from app.station_content_provenance').fetchone()['count']==284

        wahy=conn.execute('''select c.id content_id,c.lang,c.level,pv.passage_id,pv.reference provenance_reference,
            pv.source_id provenance_source_id,pv.station_content_id,p.id,p.reference,p.type,p.source,p.text,
            cs.id source_id,cs.source_name,cs.source_type,p.surah,p.ayah
            from app.station_content c join app.stations s on s.id=c.station_id
            left join app.station_content_provenance pv on pv.station_content_id=c.id
            left join public.passages p on p.id=pv.passage_id
            left join app.content_sources cs on cs.id=pv.source_id
            where s.code='WAHY-01' order by c.lang,c.level,pv.reference''').fetchall()
        wahy_variants={(r['lang'],r['level']) for r in wahy}
        assert wahy_variants=={(lang,level) for lang in ('ar','en')
            for level in ('beginner','intermediate','advanced')}
        for row in wahy:
            assert row['text'] and row['passage_id']==row['id']
            assert row['source_id']==row['provenance_source_id']
            assert row['source']==row['source_name'] and row['type']==row['source_type']
            assert row['station_content_id']==row['content_id']
            assert _provenance_reference_matches({'type':row['type'],'source':row['source'],
                'reference':row['reference'],'provenance_reference':row['provenance_reference'],
                'surah':row['surah'],'ayah':row['ayah']})
        assert any(r['reference']=='muslim:403' and r['source']=='quranlab/hadith:muslim-ar'
            for r in wahy)

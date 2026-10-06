"""Read-only data guard plus transient tap-flow test against the existing KHUTA DB.

Run with KHUTA_DB_INTEGRATION=1 and DATABASE_URL pointing at the existing islamic DB.
The tap test removes only the visitor rows it creates, cascading its temporary interactions.
"""
import os
import secrets
import json
from pathlib import Path

import pytest
from app.core.config import get_settings

pytestmark=pytest.mark.skipif(os.getenv('KHUTA_DB_INTEGRATION')!='1' or not get_settings().database_url,
    reason='requires KHUTA_DB_INTEGRATION=1 and DATABASE_URL from backend/.env or the environment')


def _async_dsn():
    value=get_settings().database_url
    if not value: raise RuntimeError('DATABASE_URL is not configured in backend/.env or the environment')
    return value.replace('postgresql+asyncpg://','postgresql://',1)


def test_existing_database_guards_and_real_tap_flow(monkeypatch):
    import psycopg
    from fastapi.testclient import TestClient
    from app.api import app,settings

    # Keep this test safe and deterministic even when a provider key exists locally.
    monkeypatch.setattr(settings,'openai_api_key',None)
    monkeypatch.setattr(settings,'gemini_api_key',None)
    original_ids=[]
    expired_card='KH-EXPIRED-'+secrets.token_hex(6).upper()
    controlled=json.loads((Path(__file__).resolve().parents[1]/'evaluation'/'results'/'CONTROLLED_STATION_CONTENT_REPORT.json').read_text(encoding='utf-8'))['content_rows']
    with psycopg.connect(_async_dsn()) as conn:
        conn.execute('set default_transaction_read_only=on')
        assert conn.execute('select count(*) from public.passages').fetchone()[0]==166774
        assert conn.execute('select count(distinct content_id) from app.embeddings').fetchone()[0]==13
        assert conn.execute('select count(*) from app.embeddings where vector_dims(embedding)<>1536').fetchone()[0]==0
        assert conn.execute("select count(*) from app.media_assets where verification_status='verified' and rights_status='permitted'").fetchone()[0]==0
        current=conn.execute('''select s.code,c.lang,c.level,c.title,c.body from app.station_content c
            join app.stations s on s.id=c.station_id where (s.code,c.lang,c.level) in
            (select unnest(%s::text[]),unnest(%s::text[]),unnest(%s::text[]))''',
            ([r['station_code'] for r in controlled],[r['lang'] for r in controlled],[r['level'] for r in controlled])).fetchall()
        expected={(r['station_code'],r['lang'],r['level'],r['title'],r['body']) for r in controlled}
        assert set(current)==expected and len(current)==30
        conn.commit()
    with psycopg.connect(_async_dsn()) as conn:
        conn.execute("insert into app.visitors(card_id,lang,level,consent,created_at,expires_at) values(%s,'ar','beginner',true,now(),now()-interval '1 hour')",(expired_card,))
        conn.commit()
    try:
        with TestClient(app) as client:
            health=client.get('/health')
            assert health.status_code==200 and health.json()['database']=='connected'
            assert health.json()['ai_configured'] is False
            assert client.get('/app').status_code==200
            def new_card(level):
                response=client.post('/visitors',json={'lang':'ar','level':level,'consent':True})
                assert response.status_code==200,response.text
                card=response.json()['card_id']; original_ids.append(card)
                return card

            beginner=new_card('beginner')
            request_id='test-'+secrets.token_hex(12)
            payload={'card_id':beginner,'station_code':'WAHY-01','request_id':request_id}
            tap=client.post('/taps',json=payload)
            assert tap.status_code==200,tap.text
            first=tap.json()
            assert first['visitor']['language']=='ar' and first['visitor']['level']=='beginner'
            assert 'interaction_id' not in first and 'id' not in first['station'] and 'debug' not in first
            assert first['content']['level']=='beginner'
            assert first['sources'] and all(s.get('source') and s.get('reference') for s in first['sources'])
            assert all('passage_id' not in s and 'source_id' not in s for s in first['sources'])
            assert all('score' not in s and 'rank' not in s for s in first['sources'])
            assert first['recommended_station'] is not None
            assert 'station_id' not in first['recommended_station']
            summary=client.get(f"/visitors/{beginner}/summary")
            assert summary.status_code==200 and summary.json()['stations_visited']==1

            replay=client.post('/taps',json=payload)
            assert replay.status_code==200 and replay.json()['station']['code']=='WAHY-01'
            assert replay.json()['content']['body']==first['content']['body']
            assert 'interaction_id' not in replay.json() and 'debug' not in replay.json()
            with psycopg.connect(_async_dsn()) as conn:
                assert conn.execute('select count(*) from app.interactions where card_id=%s',(beginner,)).fetchone()[0]==1
                conn.commit()

            ask=client.post('/ask',json={'card_id':beginner,'station_code':'WAHY-01',
                'question':'ما الآية في القرآن 96:1؟'})
            assert ask.status_code==200,ask.text
            answer=ask.json()
            assert answer['status']=='ai_unavailable' and answer['ai_generated'] is False
            assert 'debug' not in answer
            assert answer['sources'] and answer['sources'][0].get('reference')
            assert all('passage_id' not in s and 'source_id' not in s for s in answer['sources'])
            assert all('score' not in s and 'rank' not in s for s in answer['sources'])

            referral=client.post('/ask',json={'card_id':beginner,'question':'هل يجوز لي فعل ذلك في زواجي؟'})
            assert referral.status_code==200 and referral.json()['status']=='referral'
            assert referral.json()['referral'] is True and referral.json()['ai_generated'] is False

            advanced=new_card('advanced')
            advanced_tap=client.post('/taps',json={'card_id':advanced,'station_code':'WAHY-01','request_id':'test-'+secrets.token_hex(12)})
            assert advanced_tap.status_code==200,advanced_tap.text
            assert advanced_tap.json()['content']['level']=='advanced'
            assert advanced_tap.json()['content']['body']!=first['content']['body']

            assert client.post('/taps',json={'card_id':'KH-UNKNOWN-INTEGRATION','station_code':'WAHY-01'}).status_code==404
            assert client.post('/taps',json={'card_id':expired_card,'station_code':'WAHY-01'}).status_code==404
            assert client.get('/stations/10/media').json()==[]
    finally:
        with psycopg.connect(_async_dsn()) as conn:
            conn.execute('delete from app.visitors where card_id=%s',(expired_card,))
            for card in original_ids:
                conn.execute('delete from app.visitors where card_id=%s',(card,))
            conn.commit()
    with psycopg.connect(_async_dsn()) as conn:
        conn.execute('set default_transaction_read_only=on')
        assert conn.execute('select count(*) from public.passages').fetchone()[0]==166774
        after=conn.execute('''select s.code,c.lang,c.level,c.title,c.body from app.station_content c
            join app.stations s on s.id=c.station_id where (s.code,c.lang,c.level) in
            (select unnest(%s::text[]),unnest(%s::text[]),unnest(%s::text[]))''',
            ([r['station_code'] for r in controlled],[r['lang'] for r in controlled],[r['level'] for r in controlled])).fetchall()
        assert set(after)==expected and len(after)==30
        assert conn.execute('select count(*) from app.interactions where card_id=any(%s)',(original_ids,)).fetchone()[0]==0
        conn.commit()

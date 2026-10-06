import logging
import secrets
import time
import json
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AIProviderError, KhutaError
from app.ai import get_ai_provider
from app.core.logging import configure_logging, new_request_id, request_id_var
from app.db.session import engine, get_session
from app.db.repositories import ExhibitionRepository
from app.rag import RAGService
from app.schemas import AskRequest, ClassifyRequest, GenerateRequest, GeneratedAnswer, HealthOut, InteractRequest, JourneyReport, NFCInteractionRequest, RecommendationOut, StationOut, TapRequest, VisitorCreate, SourceCitation, visitor_citation, RFIDAssignRequest, RFIDResolveRequest, RFIDTapRequest
from app.services import CrowdingAnalyzer, GovernanceEngine, JourneyReportService, PresentationEngine, QuestionClassifierService, RecommendationEngine, VisitorAnalyzerService, is_station_content_question, level3_sources_approved
from app.station_flow import _content_evidence, _curated_content, process_station_tap, register_visitor
from app.rfid import assign_rfid_visitor, resolve_rfid_visitor

settings = get_settings()
configure_logging(settings.log_level)
log = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name, version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False, allow_methods=['GET','POST'], allow_headers=['Authorization','Content-Type','X-Request-ID'])
_hits: dict[str, deque] = defaultdict(deque)


async def approved_level3_sources(session: AsyncSession) -> list[str]:
    requested=settings.approved_shariah_sources
    if not requested: return []
    rows=(await session.execute(text("""select distinct source_name,rights_status,verification_status,governance_level
        from app.content_sources where source_name=any(:names) and source_type='fatwa'"""),{'names':requested})).mappings().all()
    return level3_sources_approved(requested,[dict(row) for row in rows])


@app.middleware('http')
async def request_context(request: Request, call_next):
    request_id = request.headers.get('X-Request-ID') or new_request_id()
    token = request_id_var.set(request_id)
    start = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        return response
    finally:
        route = request.scope.get('route')
        log.info('request method=%s path=%s latency_ms=%.1f', request.method, getattr(route, 'path', '/unmatched'), (time.perf_counter()-start)*1000)
        request_id_var.reset(token)


@app.middleware('http')
async def rate_limit(request: Request, call_next):
    now = time.monotonic()
    peer = request.client.host if request.client else 'unknown'
    hits = _hits[peer]
    while hits and hits[0] < now - 60:
        hits.popleft()
    if len(hits) >= settings.rate_limit_per_minute:
        raise HTTPException(429, 'Rate limit exceeded')
    hits.append(now)
    return await call_next(request)


@app.exception_handler(KhutaError)
async def khuta_error_handler(request, exc: KhutaError):
    return JSONResponse(status_code=exc.status_code, content={'error': exc.code, 'message': str(exc)})


@app.get('/health', response_model=HealthOut)
async def health(session: AsyncSession = Depends(get_session)):
    await session.execute(text('select 1'))
    return {'status':'ok','database':'connected','ai_provider':settings.llm_provider,
            'ai_model':settings.llm_model,'ai_configured':settings.ai_provider_configured}


@app.post('/ai/classify-question')
async def classify_question(body: ClassifyRequest):
    return await QuestionClassifierService().classify(body.question)


@app.post('/ai/generate-response')
async def generate_response(body: GenerateRequest, session: AsyncSession = Depends(get_session)):
    return await _ask(session,body.question,body.card_id,None,None,body.language,body.level.value,body.station_id)


async def _persist_answer(session: AsyncSession, card_id: str | None, interaction_id: int | None,
                          station_id: int | None, answer, language: str) -> bool:
    if not card_id or not answer.ai_generated or not answer.answer:
        return False
    if interaction_id is None and station_id is not None:
        interaction_id=(await session.execute(text('''select id from app.interactions where card_id=:card and station_id=:station
            order by started_at desc limit 1'''),{'card':card_id,'station':station_id})).scalar_one_or_none()
    if interaction_id is None:
        return False
    owns=(await session.execute(text('select exists(select 1 from app.interactions where id=:id and card_id=:card and (:station is null or station_id=:station))'),
        {'id':interaction_id,'card':card_id,'station':station_id})).scalar_one()
    if not owns:
        raise HTTPException(403,'The interaction does not belong to this visitor and station.')
    citations=[s.model_dump(mode='json') for s in answer.sources]
    await session.execute(text('''insert into app.generated_content(interaction_id,kind,lang,body,sources,model,created_at)
        values(:interaction,'ask_answer',:lang,:body,cast(:sources as jsonb),:model,now())'''),
        {'interaction':interaction_id,'lang':language,'body':answer.answer,'sources':json.dumps(citations,ensure_ascii=False),
         'model':f"{get_settings().llm_provider}:{get_settings().llm_model}"})
    await session.commit()
    return True


async def _require_active_visitor_consent(session: AsyncSession, card_id: str) -> None:
    row = (await session.execute(text("""select consent from app.visitors
        where card_id=:card and (expires_at is null or expires_at>now())"""),
        {"card": card_id})).first()
    if row is None:
        raise HTTPException(404, 'Unknown or expired visitor card.')
    if not row[0]:
        raise HTTPException(403, 'Visitor consent is required.')


async def _station_content_ask_answer(question: str, station_code: str, content: dict,
                                      evidence: list[dict], language: str, level: str) -> GeneratedAnswer:
    """Answer from exact station content; adapt only from validated local evidence."""
    citations=[SourceCitation(title=row.get('source') or row.get('type') or 'Source',
        source=row.get('source') or '',reference=row.get('reference'),url=row.get('url'),
        passage_id=str(row['id']),content_type=row.get('type'),text=row.get('text'),
        surah=row.get('surah'),ayah=row.get('ayah'),authenticity=row.get('authenticity'),
        grade=row.get('grade'),attribution=row.get('attribution'),rights_status=row.get('rights_status'),
        verification_status=row.get('verification_status'),governance_level=row.get('governance_level'))
        for row in evidence]
    fallback=GeneratedAnswer(status='answered',answer=content['body'],sources=citations,ai_generated=False)
    settings=get_settings()
    # _content_evidence has already enforced the local provenance mapping, source/type,
    # reference, and non-empty-text checks. Registry rights/verification values remain
    # visible as metadata; for this controlled Ask demo they are not an extra generation
    # gate once evidence passed those checks.
    evidence_is_valid=bool(evidence) and all(
        row.get('id') is not None and bool(row.get('text')) and bool(row.get('source'))
        and bool(row.get('reference')) for row in evidence)
    if not evidence_is_valid or not settings.ai_provider_configured:
        return fallback
    provider=None
    try:
        provider=get_ai_provider()
        result=await provider.generate_answer(question,evidence,language,level)
    except AIProviderError:
        return fallback
    finally:
        close=getattr(provider,'aclose',None) if provider is not None else None
        if close is not None:
            try:
                await close()
            except Exception as exc:
                log.warning('AI provider cleanup failed (%s)',type(exc).__name__)
    if result.status!='answered' or not result.ai_generated or not result.answer or not result.sources:
        return fallback
    known={str(row['id']):row for row in evidence}
    used=[]
    for citation in result.sources:
        row=known.get(str(citation.passage_id or ''))
        if (not row or citation.source!=row.get('source') or citation.reference!=row.get('reference')
                or (citation.text is not None and citation.text!=row.get('text'))):
            return fallback
        used.append(row)
    # Provider citation metadata is never authoritative. Rebuild citations from the
    # evidence rows selected by the provider after validating their passage IDs.
    local_citations=[SourceCitation(title=row.get('source') or row.get('type') or 'Source',
        source=row.get('source') or '',reference=row.get('reference'),url=row.get('url'),
        passage_id=str(row['id']),content_type=row.get('type'),text=row.get('text'),
        surah=row.get('surah'),ayah=row.get('ayah'),authenticity=row.get('authenticity'),
        grade=row.get('grade'),attribution=row.get('attribution'),rights_status=row.get('rights_status'),
        verification_status=row.get('verification_status'),governance_level=row.get('governance_level'))
        for row in used]
    return result.model_copy(update={'sources':local_citations})


async def _ask(session: AsyncSession, question: str, card_id: str | None, station_code: str | None,
                interaction_id: int | None, language: str | None, level: str | None,
                station_id: int | None=None) -> dict:
    profile=None
    if card_id:
        profile=await VisitorAnalyzerService().analyze(session,card_id)
        language,level=profile['language'],profile['level']
        consent=(await session.execute(text('select consent from app.visitors where card_id=:card'),{'card':card_id})).scalar_one_or_none()
        if not consent: raise HTTPException(403,'Visitor consent is required.')
    elif get_settings().app_env.lower()!='development':
        language,level=language or 'ar','beginner'
    language=language or 'ar'; level=level or 'beginner'
    station_context=None
    if station_code:
        station_context=(await session.execute(text('select id,code,topic from app.stations where code=:code'),{'code':station_code})).mappings().first()
        if station_context is None: raise HTTPException(404,'Unknown station.')
        station_id=station_context['id']
    elif station_id is not None:
        await ExhibitionRepository().station(session,station_id)
        station_context=(await session.execute(text('select id,code,topic from app.stations where id=:id'),{'id':station_id})).mappings().first()
    classifier=await QuestionClassifierService().classify(question, station_context=station_id is not None)
    governance=GovernanceEngine()
    base={'language':language,'level':level,
          'ai_generated':False,'referral':False,'interaction_logged':False}
    def finish(payload: dict):
        # Retrieval traces are available only through the explicit development
        # evaluation endpoint; never include them in visitor-facing /ask responses.
        return payload
    escalation=governance.escalation(classifier.category)
    if escalation:
        return finish({**base,'status':'referral','answer':None,'sources':[],'referral':True,**escalation})
    approved=await approved_level3_sources(session) if classifier.category.value=='general_shariah_question' else []
    if classifier.category.value=='general_shariah_question' and not approved:
        return finish({**base,'status':'referral','answer':None,'sources':[],'referral':True,
                'reason':'Level 3 is disabled because no exact sources have explicit approval.',
                'recommended_action':'refer_to_qualified_guide_or_scholar'})
    if classifier.safe_fallback or classifier.category.value=='unsupported_or_unclear':
        return finish({**base,'status':'insufficient_sources','answer':None,'sources':[],
                'reason':'The question did not match a supported classification rule.'})
    if (classifier.category.value=='islamic_knowledge' and station_context
            and is_station_content_question(question,station_context['code'])):
        content=await _curated_content(session,station_id,language,level)
        if content and content.get('lang')==language and content.get('level')==level:
            try:
                evidence=await _content_evidence(session,int(content['id']))
            except AIProviderError:
                evidence=[]
            if evidence:
                result=await _station_content_ask_answer(question,station_context['code'],content,
                    evidence,language,level)
                logged=await _persist_answer(session,card_id,interaction_id,station_id,result,language)
                public_result=result.model_dump(mode='json',exclude={'debug'})
                return finish({**base,**public_result,'language':language,'level':level,
                    'referral':False,'interaction_logged':logged,
                    'sources':[visitor_citation(item) for item in result.sources]})
    result=await RAGService().answer(session,question,language,classifier.category,level,station_id,approved_sources=approved)
    logged=await _persist_answer(session,card_id,interaction_id,station_id,result,language)
    public_result=result.model_dump(mode='json',exclude={'debug'})
    response={**base,**public_result,
            'language':language,'level':level,
            'referral':result.status=='referral','interaction_logged':logged,
            'sources':[visitor_citation(item) for item in result.sources]}
    return finish(response)


@app.post('/ask')
async def ask(body: AskRequest, session: AsyncSession = Depends(get_session)):
    return await _ask(session,body.question,body.card_id,body.station_code,body.interaction_id,body.language,
                      body.level.value if body.level else None)


@app.post('/visitors')
async def create_visitor(body: VisitorCreate, authorization: str | None = Header(default=None), session: AsyncSession = Depends(get_session)):
    if body.card_id:
        require_device(authorization)
    return await register_visitor(session,body.lang,body.level.value,body.consent,body.card_id)


@app.post('/taps')
async def tap(body: TapRequest, authorization: str | None = Header(default=None), session: AsyncSession = Depends(get_session)):
    require_device(authorization)
    return await process_station_tap(session,body.card_id,body.station_code,body.request_id)


@app.post('/rfid/resolve')
async def rfid_resolve(body: RFIDResolveRequest, authorization: str | None = Header(default=None), session: AsyncSession = Depends(get_session)):
    require_device(authorization)
    return await resolve_rfid_visitor(session, body.rfid_uid)


@app.post('/rfid/assign')
async def rfid_assign(body: RFIDAssignRequest, authorization: str | None = Header(default=None), session: AsyncSession = Depends(get_session)):
    require_admin(authorization)
    return await assign_rfid_visitor(session, body.rfid_uid, body.card_id)


@app.post('/rfid/tap')
async def rfid_tap(body: RFIDTapRequest, authorization: str | None = Header(default=None), session: AsyncSession = Depends(get_session)):
    require_device(authorization)
    visitor = await resolve_rfid_visitor(session, body.rfid_uid)
    return await process_station_tap(session, visitor['card_id'], body.station_code, body.request_id)


@app.get('/stations', response_model=list[StationOut])
async def stations(session: AsyncSession = Depends(get_session)):
    return await ExhibitionRepository().list_stations(session)


@app.get('/stations/{station_id}', response_model=StationOut)
async def station(station_id: int, session: AsyncSession = Depends(get_session)):
    return await ExhibitionRepository().station(session, station_id)


@app.post('/stations/{station_id}/interact')
async def station_interact(station_id: int, body: InteractRequest, authorization: str | None = Header(default=None), session: AsyncSession = Depends(get_session)):
    require_device(authorization)
    station=(await ExhibitionRepository().station(session,station_id))
    result=await process_station_tap(session,body.card_id,station['code'],body.request_id)
    result['presentation_mode']=PresentationEngine().choose(result['visitor']['language'],result['visitor']['level'])
    return result


@app.post('/interactions')
async def nfc_interaction(body: NFCInteractionRequest, authorization: str | None = Header(default=None), session: AsyncSession = Depends(get_session)):
    return await station_interact(body.station_id, body, authorization=authorization, session=session)


@app.post('/interactions/{interaction_id}/duration')
async def set_interaction_duration(interaction_id: int, body: dict, session: AsyncSession = Depends(get_session)):
    duration=body.get('duration_s')
    if not isinstance(duration,int) or not 0<=duration<=7200:
        raise HTTPException(400,'Duration is outside the supported range.')
    updated=(await session.execute(text('update app.interactions set duration_s=:duration where id=:id returning id'),
        {'duration':duration,'id':interaction_id})).scalar_one_or_none()
    if updated is None: raise HTTPException(404,'Interaction not found.')
    await session.commit()
    return {'ok':True}


@app.get('/visitors/{card_id}/summary')
async def visitor_summary(card_id: str, session: AsyncSession = Depends(get_session)):
    await _require_active_visitor_consent(session, card_id)
    profile=await VisitorAnalyzerService().analyze(session,card_id)
    rows=(await session.execute(text('''select s.code,s.name,i.started_at,i.duration_s from app.interactions i
        join app.stations s on s.id=i.station_id where i.card_id=:card order by i.started_at'''),{'card':card_id})).mappings().all()
    return {'card_id':card_id,'lang':profile['language'],'level':profile['level'],
        'stations_visited':len({r['code'] for r in rows}),'total_seconds':sum(r['duration_s'] or 0 for r in rows),
        'journey':[{'station_code':r['code'],'station_name':r['name'],'at':r['started_at'],'duration_s':r['duration_s']} for r in rows]}


@app.delete('/visitors/{card_id}')
async def delete_visitor(card_id: str, session: AsyncSession = Depends(get_session)):
    deleted=(await session.execute(text('delete from app.visitors where card_id=:card returning card_id'),{'card':card_id})).scalar_one_or_none()
    if deleted is None: raise HTTPException(404,'Visitor card not found.')
    await session.commit()
    return {'deleted':True}


@app.get('/app',include_in_schema=False)
async def app_screen():
    require_development()
    return FileResponse(Path(__file__).resolve().parents[2]/'khutta'/'demo.html')


@app.get('/stations/{station_id}/media')
async def approved_station_media(station_id: int, session: AsyncSession = Depends(get_session)):
    await ExhibitionRepository().station(session,station_id)
    from app.station_flow import _media
    return await _media(session,station_id,'en')


@app.post('/ai/recommend-next-station', response_model=RecommendationOut)
async def recommend(body: InteractRequest, station_id: int | None = None, session: AsyncSession = Depends(get_session)):
    await _require_active_visitor_consent(session, body.card_id)
    profile=await VisitorAnalyzerService().analyze(session,body.card_id)
    result = await RecommendationEngine().recommend(session, body.card_id, station_id, profile['language'])
    return {'recommended_station':result['recommended_station'],'reason':result['reason']}


@app.get('/visitor/{card_id}')
async def visitor(card_id: str, session: AsyncSession = Depends(get_session)):
    await _require_active_visitor_consent(session, card_id)
    return await VisitorAnalyzerService().analyze(session, card_id)


@app.get('/visitor/{card_id}/report', response_model=JourneyReport)
async def report(card_id: str, session: AsyncSession = Depends(get_session)):
    await _require_active_visitor_consent(session, card_id)
    return await JourneyReportService().build(session, card_id)


@app.get('/crowding/stations')
async def crowding(session: AsyncSession = Depends(get_session)):
    return await CrowdingAnalyzer().all_stations(session)


@app.get('/crowding/stations/{station_id}')
async def station_crowding(station_id: int, session: AsyncSession = Depends(get_session)):
    await ExhibitionRepository().station(session, station_id)
    return await CrowdingAnalyzer().station(session, station_id)


def require_admin(authorization: str | None):
    if not settings.admin_api_key:
        raise HTTPException(503, 'Admin authentication is not configured')
    if not secrets.compare_digest(authorization or '', f'Bearer {settings.admin_api_key}'):
        raise HTTPException(401, 'Unauthorized')


def require_device(authorization: str | None):
    if settings.app_env.lower() == 'production' and not settings.device_api_key:
        raise HTTPException(503, 'Device authentication is not configured')
    if settings.device_api_key and not secrets.compare_digest(authorization or '', f'Bearer {settings.device_api_key}'):
        raise HTTPException(401, 'Unauthorized')


@app.get('/analytics/dashboard')
async def dashboard(authorization: str | None = Header(default=None), session: AsyncSession = Depends(get_session)):
    require_admin(authorization)
    counts = (await session.execute(text('select (select count(*) from app.visitors)::int visitors,(select count(*) from app.interactions)::int interactions,(select count(*) from app.stations)::int stations'))).mappings().one()
    langs = (await session.execute(text('select lang,count(*)::int count from app.visitors group by lang order by count desc'))).mappings().all()
    levels = (await session.execute(text('select level,count(*)::int count from app.visitors group by level order by level'))).mappings().all()
    crowding_trends = (await session.execute(text("select date_trunc('hour',started_at) bucket,station_id,count(*) filter(where duration_s is null)::int unresolved_interactions from app.interactions where started_at >= now()-interval '24 hours' group by 1,2 order by 1,2"))).mappings().all()
    return {'counts':dict(counts),'language_distribution':[dict(x) for x in langs],'visitor_levels':[dict(x) for x in levels],'crowding_trends':[dict(x) for x in crowding_trends]}


@app.get('/analytics/stations')
async def analytics_stations(authorization: str | None = Header(default=None), session: AsyncSession = Depends(get_session)):
    require_admin(authorization)
    rows=(await session.execute(text('select s.id,s.code,s.name,count(i.id)::int interactions,coalesce(avg(i.duration_s),0)::float avg_duration_seconds from app.stations s left join app.interactions i on i.station_id=s.id group by s.id order by interactions desc'))).mappings().all()
    levels=(await session.execute(text('select v.level,count(*)::int interactions from app.interactions i join app.visitors v on v.card_id=i.card_id group by v.level order by v.level'))).mappings().all()
    return {'stations':[dict(r) for r in rows],'interactions_by_visitor_level':[dict(r) for r in levels]}


@app.get('/analytics/questions')
async def analytics_questions(authorization: str | None = Header(default=None), session: AsyncSession = Depends(get_session)):
    require_admin(authorization)
    rows=(await session.execute(text("select kind,count(*)::int count from app.generated_content group by kind order by count desc"))).mappings().all()
    return {'generated_content_by_kind':[dict(r) for r in rows], 'top_questions': []}


@app.on_event('shutdown')
async def shutdown():
    await engine.dispose()



def require_development():
    if settings.app_env.lower() != 'development':
        raise HTTPException(404, 'Not found')


@app.get('/ai-playground', include_in_schema=False)
async def ai_playground_page():
    require_development()
    return FileResponse(Path(__file__).resolve().parents[2] / 'khutta' / 'ai-playground.html')


@app.get('/ai-evaluation', include_in_schema=False)
async def ai_evaluation_page():
    require_development()
    return FileResponse(Path(__file__).resolve().parents[2] / 'khutta' / 'ai-evaluation.html')


@app.post('/dev/ai/pipeline')
async def debug_ai_pipeline(body: GenerateRequest, session: AsyncSession = Depends(get_session)):
    """Development-only full pipeline inspection. Never stores interactions or changes source passages."""
    require_development()
    started=time.perf_counter()
    classifier = await QuestionClassifierService().classify(body.question, station_context=body.station_id is not None)
    governance = GovernanceEngine()
    escalation = governance.escalation(classifier.category)
    approved_sources = await approved_level3_sources(session) if classifier.category.value == 'general_shariah_question' else []
    level3_blocked = classifier.category.value == 'general_shariah_question' and not approved_sources
    pipeline = {
        'question': body.question,
        'classification': classifier.model_dump(mode='json'),
        'governance': {
            'level': governance.level_for(classifier.category),
            'decision': 'escalate' if escalation else ('blocked_unapproved_sources' if level3_blocked else ('abstain' if classifier.safe_fallback else 'retrieve')),
            'escalation_required': bool(escalation) or classifier.safe_fallback or level3_blocked,
            'reason': escalation.get('reason') if escalation else ('Level 3 is blocked until exact trusted sources are approved.' if level3_blocked else ('No supported classification rule matched.' if classifier.safe_fallback else None)),
        },
        'retrieved_passages': [],
        'answer': None,
        'citations': [],
        'ai_status': 'not_called',
        'recommended_next_station': None,
        'interaction_logged': False,
        'level_3_enabled': bool(approved_sources),
    }
    def finish():
        pipeline['debug']={'card_id':body.card_id,'station_id':body.station_id,
            'retrieved_passage_ids':[p.get('id') for p in pipeline['retrieved_passages']],
            'lexical_scores':[{'id':p.get('id'),'score':p.get('score'),'channels':p.get('retrieval_channels')} for p in pipeline['retrieved_passages']],
            'vector_scores_available':any('vector' in (p.get('retrieval_channels') or []) for p in pipeline['retrieved_passages']),
            'governance_decision':pipeline['governance']['decision'],'llm_provider':settings.llm_provider,
            'llm_model':settings.llm_model if settings.ai_provider_configured else None,
            'latency_ms':round((time.perf_counter()-started)*1000,1)}
        return pipeline
    if body.card_id:
        try:
            active = (await session.execute(text('select consent from app.visitors where card_id=:card and (expires_at is null or expires_at>now())'), {'card':body.card_id})).mappings().first()
            if not active:
                raise HTTPException(404, 'Unknown or expired visitor card.')
            if not active['consent']:
                raise HTTPException(403, 'Visitor consent is required.')
            profile = await VisitorAnalyzerService().analyze(session, body.card_id)
            if body.station_id is not None:
                pipeline['recommended_next_station'] = await RecommendationEngine().recommend(session, body.card_id, body.station_id,profile['language'])
        except HTTPException as exc:
            pipeline['visitor_error'] = {'code': 'visitor_not_authorized', 'message': exc.detail}
            pipeline['ai_status'] = 'visitor_not_authorized'
            pipeline['governance']['decision'] = 'deny'
            return finish()
        except KhutaError as exc:
            pipeline['visitor_error'] = {'code': exc.code, 'message': str(exc)}
            pipeline['ai_status'] = 'visitor_not_authorized'
            pipeline['governance']['decision'] = 'deny'
            return finish()
    if escalation:
        pipeline['escalation'] = escalation
        return finish()
    if level3_blocked:
        pipeline['ai_status'] = 'level_3_blocked_no_approved_sources'
        pipeline['escalation'] = {'escalation_required': True, 'reason': pipeline['governance']['reason'], 'recommended_action': 'refer_to_qualified_guide_or_scholar'}
        return finish()
    if classifier.safe_fallback:
        pipeline['ai_status'] = 'abstained_unsupported_or_unclear'
        return finish()
    rag = RAGService()
    passages = await rag.retrieve(session, body.question, body.language, classifier.category, body.level.value, station_id=body.station_id, approved_sources=approved_sources)
    pipeline['retrieved_passages'] = [{k: p.get(k) for k in ('id','type','language','source','reference','url','score','text','surah','ayah','authenticity','grade','retrieval_channels','rights_status','verification_status','governance_level')} for p in passages]
    if not passages:
        pipeline['ai_status'] = 'no_evidence'
        return finish()
    if not settings.ai_provider_configured:
        pipeline['ai_status'] = 'AI_PROVIDER_NOT_CONFIGURED'
        return finish()
    try:
        from app.ai import get_ai_provider
        answer = await get_ai_provider().generate_answer(body.question, passages, body.language,body.level.value)
        pipeline['answer'] = answer.answer
        pipeline['citations'] = [item.model_dump(mode='json') for item in answer.sources]
        pipeline['ai_status'] = answer.status
    except KhutaError as exc:
        pipeline['ai_status'] = exc.code
        pipeline['generation_error'] = str(exc)
    return finish()


@app.get('/dev/visitors')
async def development_visitors(session: AsyncSession = Depends(get_session)):
    require_development()
    rows = (await session.execute(text("select card_id,lang,level from app.visitors where consent=true and (expires_at is null or expires_at>now()) order by created_at desc limit 20"))).mappings().all()
    return [dict(row) for row in rows]


@app.get('/dev/evaluation-results')
async def development_evaluation_results():
    require_development()
    path = Path(__file__).resolve().parents[1] / 'evaluation' / 'results' / 'evaluation_results.json'
    if not path.exists():
        raise HTTPException(404, 'Baseline evaluation has not been run yet.')
    return FileResponse(path, media_type='application/json')

import asyncio

from app.core.errors import GeminiRateLimitError
from app.schemas import GeneratedAnswer, SourceCitation
from app.services import (QuestionClassifierService, crowding_status, is_station_content_question,
    recommendation_rank, recommendation_station_pool, CrowdingAnalyzer)


def test_station_scoped_educational_questions_are_supported():
    classifier=QuestionClassifierService()
    for question in ('ما معنى التوحيد؟','ما هو التوحيد؟','اشرح لي التوحيد',
                     'ماذا تعلمنا في هذه المحطة؟','اشرح لي هذا الموضوع','ما معنى هذه الآية؟',
                     'Tell me the story of this station'):
        result=asyncio.run(classifier.classify(question,station_context=True))
        assert result.category.value=='islamic_knowledge',question
    for question in ('What is Tawheed?','Explain Tawheed.','What does this station teach?',
                     'Explain this topic.','What does this verse mean?'):
        result=asyncio.run(classifier.classify(question,station_context=True))
        assert result.category.value=='islamic_knowledge',question


def test_generic_station_educational_question_requires_station_context():
    result=asyncio.run(QuestionClassifierService().classify('ما معنى هذه الآية؟'))
    assert result.category.value=='unsupported_or_unclear'
    result=asyncio.run(QuestionClassifierService().classify('ما معنى التوحيد؟'))
    assert result.category.value=='islamic_knowledge'


def test_personal_fatwa_remains_higher_priority_than_station_context():
    classifier=QuestionClassifierService()
    for question in ('هل يجوز لي أن أفعل كذا؟','أنا فعلت كذا فماذا يجب علي؟','ما حكم حالتي؟','هل علي إثم في حالتي؟'):
        result=asyncio.run(classifier.classify(question,station_context=True))
        assert result.category.value=='personal_fatwa',question


def test_station_content_fallback_matches_only_relevant_educational_topic():
    assert is_station_content_question('ما معنى التوحيد؟','TAWHEED-01')
    assert is_station_content_question('What is Tawheed?','TAWHEED-01')
    assert is_station_content_question('Tell me the story of Badr','BADR-01')
    assert is_station_content_question('احك لي قصة هذه المحطة','BADR-01')
    assert is_station_content_question('ما معنى هذه الآية؟','QURAN-01')
    assert not is_station_content_question('What happened at Badr?','TAWHEED-01')
    assert not is_station_content_question('Tawheed in a historical timeline','TAWHEED-01')


def test_station_content_selection_filters_exact_station_language_and_level():
    from app.station_flow import _curated_content
    class Result:
        def mappings(self): return self
        def first(self): return {'id':41,'lang':'ar','level':'intermediate'}
    class Session:
        statement=''
        params=None
        async def execute(self,statement,params):
            self.statement=str(statement).casefold(); self.params=params
            return Result()
    session=Session()
    selected=asyncio.run(_curated_content(session,24,'ar','intermediate'))
    assert selected['lang']=='ar' and selected['level']=='intermediate'
    assert 'station_id=:station and lang=:lang and level=:level' in session.statement
    assert session.params=={'station':24,'lang':'ar','level':'intermediate'}


def test_crowding_thresholds_are_deterministic():
    assert [crowding_status(n,8) for n in (0,2,3,7,8,12)]==['low','low','medium','medium','high','high']


def test_crowding_query_excludes_stale_and_completed_interactions():
    class Result:
        def scalar_one(self): return 2
    class Session:
        statement=''
        params=None
        async def execute(self,statement,params):
            self.statement=str(statement).casefold(); self.params=params
            return Result()
    session=Session()
    result=asyncio.run(CrowdingAnalyzer().station(session,24))
    assert 'duration_s is null' in session.statement
    assert 'started_at >= now()' in session.statement
    assert session.params['mins']>0
    assert result['active_interactions']==2 and result['status']=='low'
    assert 'no physical occupancy sensor' in result['estimate']


def test_recommendation_pool_excludes_experimental_stations_and_scopes_seerah_details():
    normal=recommendation_station_pool('TAWHEED-01')
    assert len(normal)==8
    assert set(normal)=={'TAWHEED-01','KAABA-01','SALAH-01','SEERAH-01','HISTORY-01','QURAN-01','WUDU-01','ZAKAT-01'}
    assert 'ST-01' not in normal and 'ST-02' not in normal
    journey=recommendation_station_pool('SEERAH-01')
    assert set(journey)==set(normal)|{'WAHY-01','HIJRAH-01','BADR-01'}


def test_recommendation_uses_crowding_only_after_relevance():
    assert not recommendation_rank(True,9,1)<recommendation_rank(True,2,2)
    assert recommendation_rank(True,9,1)<recommendation_rank(False,0,2)
    assert recommendation_rank(True,2,1)<recommendation_rank(True,9,2)


def _station_content_fixture():
    content={'id':40,'lang':'ar','level':'intermediate','title':'التوحيد','body':'Stored evidence-bounded story.'}
    row={'id':'p-1','type':'quran','source':'مصحف حفص','reference':'112:1','text':'قُلْ هُوَ اللَّهُ أَحَدٌ',
        'verification_status':'verified','rights_status':'permitted','governance_level':'APPROVED_LEVEL_2'}
    return content,[row]


def test_station_ask_falls_back_to_exact_content_when_gemini_is_rate_limited(monkeypatch):
    import app.api as api

    class Provider:
        closed=False
        async def generate_answer(self,*args,**kwargs):
            raise GeminiRateLimitError('HTTP 429')
        async def aclose(self): self.closed=True

    provider=Provider()
    monkeypatch.setattr(api,'get_ai_provider',lambda:provider)
    monkeypatch.setattr(api,'get_settings',lambda:type('Settings',(),{'ai_provider_configured':True})())
    content,evidence=_station_content_fixture()
    result=asyncio.run(api._station_content_ask_answer('ما معنى التوحيد؟','TAWHEED-01',content,evidence,'ar','intermediate'))
    assert result.answer==content['body']
    assert result.sources[0].reference=='112:1'
    assert result.ai_generated is False and result.status=='answered'
    assert provider.closed


def test_station_ask_allows_controlled_local_evidence_despite_review_metadata(monkeypatch):
    import app.api as api
    from app.schemas import GeneratedAnswer, SourceCitation

    class Provider:
        called=False
        async def generate_answer(self,*args,**kwargs):
            self.called=True
            return GeneratedAnswer(status='answered',answer='الله واحد، والعبادة له.',ai_generated=True,
                sources=[SourceCitation(title='Fabricated title',source='مصحف حفص',reference='112:1',
                    passage_id='p-1',content_type='quran',text='قُلْ هُوَ اللَّهُ أَحَدٌ',url='https://fake.invalid')])
        async def aclose(self): pass
    provider=Provider()
    monkeypatch.setattr(api,'get_ai_provider',lambda:provider)
    monkeypatch.setattr(api,'get_settings',lambda:type('Settings',(),{'ai_provider_configured':True})())
    content,evidence=_station_content_fixture()
    evidence[0]['verification_status']='unverified'
    evidence[0]['rights_status']='needs_review'
    result=asyncio.run(api._station_content_ask_answer('ما معنى التوحيد؟','TAWHEED-01',content,evidence,'ar','intermediate'))
    assert provider.called
    assert result.answer=='الله واحد، والعبادة له.' and result.ai_generated is True
    assert result.sources[0].title=='مصحف حفص'
    assert result.sources[0].url is None
    assert result.sources[0].reference=='112:1'


def test_station_ask_without_evidence_does_not_call_gemini(monkeypatch):
    import app.api as api
    def unexpected_call(): raise AssertionError('Gemini must not be called without evidence')
    monkeypatch.setattr(api,'get_ai_provider',unexpected_call)
    monkeypatch.setattr(api,'get_settings',lambda:type('Settings',(),{'ai_provider_configured':True})())
    content,_=_station_content_fixture()
    result=asyncio.run(api._station_content_ask_answer('ما معنى التوحيد؟','TAWHEED-01',content,[],'ar','intermediate'))
    assert result.status=='answered' and result.ai_generated is False
    assert result.answer==content['body'] and result.sources==[]


def test_personal_fatwa_ask_is_referred_before_provider(monkeypatch):
    import app.api as api
    class Result:
        def mappings(self): return self
        def first(self): return {'id':24,'code':'TAWHEED-01','topic':'Tawheed'}
    class Session:
        async def execute(self,*args,**kwargs): return Result()
    def unexpected_call(): raise AssertionError('Personal fatwa must never call Gemini')
    monkeypatch.setattr(api,'get_ai_provider',unexpected_call)
    result=asyncio.run(api._ask(Session(),'هل يجوز لي الطلاق في حالتي؟',None,'TAWHEED-01',None,'ar','intermediate'))
    assert result['status']=='referral'
    assert result['ai_generated'] is False and result['referral'] is True
    assert result['escalation_required'] is True


def test_normal_station_story_path_does_not_call_ai_provider():
    import inspect
    from app.station_flow import process_station_tap
    source=inspect.getsource(process_station_tap)
    assert 'get_ai_provider' not in source
    assert "'ai_generated':False" in source
    assert "'ai_status':'database_content'" in source

import asyncio
import json
from types import SimpleNamespace

from app.ai import OpenAIProvider, _normalize_gemini_response
from app.core.errors import AIProviderError
from app.schemas import SourceCitation, visitor_citation


class FakeCompletions:
    async def create(self, **kwargs):
        message=SimpleNamespace(content=json.dumps({'status':'answered','answer':'A short explanation based on this passage.',
            'used_sources':['valid'],'presentation_mode':'text','recommended_station':None}))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)],usage=None)


class FakeClient:
    def __init__(self):
        self.chat=SimpleNamespace(completions=FakeCompletions())


def test_provider_returns_exact_retrieved_citation_metadata():
    provider=object.__new__(OpenAIProvider)
    provider.client=FakeClient()
    provider.settings=SimpleNamespace(llm_model='test-model')
    context=[{'id':'valid','type':'quran','source':'approved source','reference':'2:1','text':'Exact verse from database','surah':2,'ayah':1}]
    answer=asyncio.run(provider.generate_answer('question',context,'en'))
    assert len(answer.sources)==1
    assert answer.sources[0].source=='approved source'
    assert answer.sources[0].passage_id=='valid'
    assert answer.sources[0].text=='Exact verse from database'
    assert answer.ai_generated is True


def test_provider_rejects_unknown_source_ids():
    class InvalidCompletions:
        async def create(self, **kwargs):
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({
                'status':'answered','answer':'Unsupported answer.','used_sources':['invented'],
                'presentation_mode':'text','recommended_station':None})))],usage=None)
    provider=object.__new__(OpenAIProvider)
    provider.client=SimpleNamespace(chat=SimpleNamespace(completions=InvalidCompletions()))
    provider.settings=SimpleNamespace(llm_model='test-model')
    try:
        asyncio.run(provider.generate_answer('question',[{'id':'valid','type':'quran','source':'src','reference':'2:1','text':'text'}],'en'))
    except AIProviderError:
        return
    raise AssertionError('unknown source IDs must be rejected')


def test_provider_does_not_generate_long_quran_quotes():
    quote=' '.join(['هذا نص قرآني من قاعدة البيانات']*8)
    class QuoteCompletions:
        async def create(self, **kwargs):
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({
                'status':'answered','answer':quote,'used_sources':['valid'],
                'presentation_mode':'text','recommended_station':None})))],usage=None)
    provider=object.__new__(OpenAIProvider)
    provider.client=SimpleNamespace(chat=SimpleNamespace(completions=QuoteCompletions()))
    provider.settings=SimpleNamespace(llm_model='test-model')
    try:
        asyncio.run(provider.generate_answer('question',[{'id':'valid','type':'quran','source':'src','reference':'2:1','text':quote}],'ar'))
    except AIProviderError:
        return
    raise AssertionError('verbatim Quran quotations must be served from the database')


def test_visitor_citation_omits_internal_ids_and_governance_debug():
    citation=SourceCitation(title='Hafs Quran',source='مصحف حفص',reference='96:1',
        passage_id='internal-hash',content_type='quran',text='Exact DB verse',
        verification_status='verified',rights_status='permitted',governance_level='APPROVED_LEVEL_2')
    public=visitor_citation(citation)
    assert public['type']=='quran'
    assert public['reference']=='96:1' and public['text']=='Exact DB verse'
    assert 'passage_id' not in public and 'governance_level' not in public


def test_known_gemini_response_aliases_normalize_to_visitor_contract():
    from app.schemas import StructuredAIAnswer
    result=_normalize_gemini_response({'status':'success','answer':'A concise answer.',
        'used_sources':['valid'],'presentation_mode':'narrative','recommended_station':None})
    parsed=StructuredAIAnswer.validate_answer(result)
    assert parsed.status=='answered' and parsed.presentation_mode=='storytelling'


def test_gemini_abstention_with_null_presentation_mode_is_validated_safely():
    from app.schemas import StructuredAIAnswer
    result=_normalize_gemini_response({'status':'insufficient_sources','answer':None,
        'used_sources':[],'presentation_mode':None,'recommended_station':None})
    parsed=StructuredAIAnswer.validate_answer(result)
    assert parsed.status=='insufficient_sources' and parsed.presentation_mode=='text'

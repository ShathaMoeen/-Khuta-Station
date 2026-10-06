import asyncio

from app.ai import _citation_from_passage
from app.rag import RAGService
from app.schemas import GeneratedAnswer, QuestionCategory, SourceCitation


class EmptyPassageSource:
    async def search(self, *args, **kwargs):
        return []


class OnePassageSource:
    async def search(self, *args, **kwargs):
        return [{'id':'local-1','type':'hadith','language':'ar','source':'collection',
            'reference':'bukhari:3','url':'https://example.invalid','text':'Exact database text',
            'authenticity':'sahih','grade':'grade-field','surah':None,'ayah':None,
            'verification_status':'verified','rights_status':'permitted','governance_level':'APPROVED_LEVEL_2'}]


class ForgedCitationProvider:
    async def generate_answer(self, question, context, language, level='beginner'):
        return GeneratedAnswer(status='answered',answer='Unsupported claim',ai_generated=True,
            sources=[SourceCitation(title='fake',source='invented',reference='wrong',passage_id='not-retrieved')])


def test_rag_returns_insufficient_sources_without_evidence():
    result=asyncio.run(RAGService(passage_source=EmptyPassageSource()).answer(
        None,'question','ar',QuestionCategory.islamic_knowledge))
    assert result.status=='insufficient_sources'
    assert result.answer is None
    assert result.sources==[]


def test_rag_withholds_answer_when_citation_does_not_match_retrieved_row():
    rag=RAGService(provider=ForgedCitationProvider(),passage_source=OnePassageSource())
    result=asyncio.run(rag.answer(None,'question','ar',QuestionCategory.islamic_knowledge))
    assert result.status=='insufficient_sources'
    assert result.answer is None
    assert result.sources==[]
    assert 'Citation validation failed' in result.reason


def test_exact_hadith_metadata_and_text_are_propagated_from_row():
    citation=_citation_from_passage({'id':'p-1','type':'hadith','source':'collection',
        'reference':'bukhari:3','text':'exact Arabic text','authenticity':'sahih','grade':'grade-field'})
    assert citation.passage_id=='p-1'
    assert citation.text=='exact Arabic text'
    assert citation.authenticity=='sahih'
    assert citation.grade=='grade-field'

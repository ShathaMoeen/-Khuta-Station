import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import AIProvider, get_ai_provider
from app.core.config import get_settings
from app.core.errors import AIProviderError
from app.schemas import GeneratedAnswer, QuestionCategory
from app.sources import ContentSource, ExhibitionContentSource, PassageContentSource
from app.services import TrustedSourceRouter, is_controlled_station_passage
from app.storytelling import is_story_request

log = logging.getLogger(__name__)


class RAGService:
    def __init__(self, provider: AIProvider | None = None, exhibition_source: ContentSource | None = None, passage_source: PassageContentSource | None = None):
        self.router = TrustedSourceRouter()
        self.provider = provider
        self.exhibition_source = exhibition_source or ExhibitionContentSource()
        self.passage_source = passage_source or PassageContentSource()

    async def retrieve(self, session: AsyncSession, question: str, language: str, category: QuestionCategory, level: str = 'beginner', limit: int = 6, station_id: int | None = None, approved_sources: list[str] | None = None, retrieval_mode: str = 'hybrid') -> list[dict]:
        types, source_allowlist = self.router.allowed(category, approved_sources)
        if not types:
            return []
        topic=None
        if station_id is not None:
            topic=(await session.execute(text('select topic from app.stations where id=:id'),{'id':station_id})).scalar_one_or_none()
        if category == QuestionCategory.general_knowledge:
            return await self.exhibition_source.search(session,question,language,level,limit,station_id,topic,retrieval_mode)
        return await self.passage_source.search(session,question,language,level,limit,station_id,topic,types,source_allowlist,retrieval_mode)

    async def answer(self, session: AsyncSession, question: str, language: str, category: QuestionCategory, level: str = 'beginner', station_id: int | None = None, approved_sources: list[str] | None = None) -> GeneratedAnswer:
        context = await self.retrieve(session, question, language, category, level, station_id=station_id, approved_sources=approved_sources)
        log.info('rag_retrieval category=%s language=%s level=%s retrieval_count=%s', category.value, language, level, len(context))
        if not context:
            return GeneratedAnswer(status='insufficient_sources',answer=None,sources=[],ai_generated=False,
                reason='No relevant database evidence was retrieved.',debug={'retrieval_count':0,'ranking':[]})
        retrieval_debug={'retrieval_count':len(context),'ranking':[{'id':str(p['id']),'score':p.get('score'),
            'channels':p.get('retrieval_channels',[]),'source':p.get('source'),'reference':p.get('reference'),
            'verification_status':p.get('verification_status'),'rights_status':p.get('rights_status'),
            'governance_level':p.get('governance_level')} for p in context]}
        if category == QuestionCategory.islamic_knowledge:
            trusted=[p for p in context if (
                p.get('verification_status')=='verified' and p.get('rights_status')=='permitted'
                and p.get('governance_level') in {'APPROVED_LEVEL_1','APPROVED_LEVEL_2'})
                or (station_id is not None and is_controlled_station_passage(p))]
        elif category == QuestionCategory.general_shariah_question:
            trusted=[p for p in context if p.get('verification_status')=='verified'
                and p.get('rights_status')=='permitted' and p.get('governance_level')=='APPROVED_LEVEL_3'
                and p.get('source') in (approved_sources or [])]
        else:
            trusted=context
        if not trusted:
            return GeneratedAnswer(status='insufficient_sources',answer=None,
                sources=[_citation(p) for p in context],ai_generated=False,
                reason='Retrieved records exist, but none pass the required source verification, rights, and governance approvals.',
                debug=retrieval_debug)
        try:
            provider = self.provider or get_ai_provider()
            try:
                result = await provider.generate_answer(question, trusted, language, level)
            finally:
                if self.provider is None:
                    close=getattr(provider,'aclose',None)
                    if close is not None: await close()
        except AIProviderError as exc:
            return GeneratedAnswer(status='ai_unavailable',answer=None,
                sources=[_citation(p) for p in context],ai_generated=False,reason=exc.code,debug=retrieval_debug)
        retrieved={str(p['id']):p for p in trusted}
        for citation in result.sources:
            key=citation.passage_id or (str(citation.station_content_id) if citation.station_content_id is not None else None)
            matched=retrieved.get(key or '')
            if not matched or citation.source!=matched.get('source') or citation.reference!=matched.get('reference'):
                return GeneratedAnswer(status='insufficient_sources',answer=None,sources=[],ai_generated=False,
                    reason='Citation validation failed; the answer was withheld.',debug=retrieval_debug)
            if citation.text is not None and citation.text!=matched.get('text'):
                return GeneratedAnswer(status='insufficient_sources',answer=None,sources=[],ai_generated=False,
                    reason='Quoted source text did not exactly match the database; the answer was withheld.',debug=retrieval_debug)
        if result.status=='answered' and (not result.answer or not result.sources):
            return GeneratedAnswer(status='insufficient_sources',answer=None,sources=[],ai_generated=False,
                reason='An answer without validated citations was withheld.',debug=retrieval_debug)
        updates={'debug':retrieval_debug}
        if result.status=='answered' and is_story_request(question):
            updates['presentation_mode']='storytelling'
        return result.model_copy(update=updates)


def _citation(passage: dict):
    from app.ai import _citation_from_passage
    return _citation_from_passage(passage)


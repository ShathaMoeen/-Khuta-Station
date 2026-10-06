from collections import Counter
from datetime import datetime, timezone
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import VisitorNotFoundError
from app.schemas import Classification, QuestionCategory, VisitorLevel
from app.storytelling import is_story_request

settings = get_settings()

CONTROLLED_QURAN_COORDS={(3,123),(3,124),(3,125),(3,126),(3,127),(9,40),
    (96,1),(96,2),(96,3),(96,4),(96,5)}
CONTROLLED_HADITH_REFERENCES={'bukhari:3','bukhari:5807'}
FINAL_VISITOR_STATION_CODES=('TAWHEED-01','KAABA-01','SALAH-01','SEERAH-01',
    'HISTORY-01','QURAN-01','WUDU-01','ZAKAT-01')
SEERAH_JOURNEY_STATION_CODES=('WAHY-01','HIJRAH-01','BADR-01')


def crowding_status(active_interactions: int, high_threshold: int=8) -> str:
    if active_interactions>=high_threshold: return 'high'
    if active_interactions>=3: return 'medium'
    return 'low'


def recommendation_station_pool(current_station_code: str | None) -> tuple[str,...]:
    if current_station_code=='SEERAH-01':
        return FINAL_VISITOR_STATION_CODES+SEERAH_JOURNEY_STATION_CODES
    return FINAL_VISITOR_STATION_CODES


def recommendation_rank(continues_topic: bool, active_interactions: int, station_id: int) -> tuple[int,int,int]:
    """Keep relevance primary; use current activity to break relevance ties."""
    return (0 if continues_topic else 1,active_interactions,station_id)


def is_controlled_station_passage(row: dict) -> bool:
    """Check the explicitly approved demo source IDs and references only.

    Callers must also require that the record came through a controlled
    ``app.station_passages`` station filter. This does not alter source rights or
    verification metadata.
    """
    if row.get('governance_level')!='APPROVED_LEVEL_2': return False
    source_id=row.get('source_id')
    if row.get('type')=='quran':
        return source_id==30 and row.get('source')=='مصحف حفص' and (row.get('surah'),row.get('ayah')) in CONTROLLED_QURAN_COORDS
    if row.get('type')=='hadith':
        return source_id==2 and row.get('source')=='quranlab/hadith:bukhari-ar' and row.get('reference') in CONTROLLED_HADITH_REFERENCES
    return False


class VisitorAnalyzerService:
    async def analyze(self, session: AsyncSession, card_id: str) -> dict:
        visitor = (await session.execute(text("select lang, level from app.visitors where card_id=:card and (expires_at is null or expires_at>now())"), {'card': card_id})).mappings().first()
        if not visitor:
            raise VisitorNotFoundError('Unknown or expired visitor card')
        rows = (await session.execute(text("select s.topic from app.interactions i join app.stations s on s.id=i.station_id where i.card_id=:card and s.topic is not null"), {'card': card_id})).all()
        topics = Counter(row[0] for row in rows if row[0])
        visited=(await session.execute(text('''select distinct s.code from app.interactions i join app.stations s on s.id=i.station_id
            where i.card_id=:card order by s.code'''),{'card':card_id})).scalars().all()
        return {'language': visitor['lang'], 'level': visitor['level'], 'visited_stations': list(visited), 'interests': [t for t, _ in topics.most_common(5)]}


STATION_EDUCATIONAL_PROMPTS=('what does this station teach','what does the station teach','what is this station about',
    'explain this topic','what does this topic mean','what does this verse mean','explain this verse',
    'tell me the story of this station','tell me the story of this topic',
    'ماذا تعلمنا في هذه المحطة','ماذا تعلمنا في المحطة','اشرح لي هذا الموضوع','اشرح هذا الموضوع',
    'ما معنى هذه الآية','ما معنى الآية','اشرح هذه الآية','ما هو موضوع هذه المحطة',
    'احك لي قصة هذه المحطة','احكي لي قصة هذه المحطة','حدثني عن قصة هذه المحطة')


def is_station_content_question(question: str, station_code: str) -> bool:
    """Conservatively match a station-scoped educational question to its topic."""
    q=question.casefold()
    if any(term in q for term in STATION_EDUCATIONAL_PROMPTS):
        return True
    educational_intents=('what is','what does','explain','define','meaning','tell me about','describe','story','narrative',
        'ما معنى','ما هو','اشرح','عرّف','عرف','حدثني عن','تكلم عن','قصة','احك','احكي')
    if not any(term in q for term in educational_intents):
        return False
    topics={
        'TAWHEED-01':('tawheed','tawhid','التوحيد','توحيد'),
        'KAABA-01':('kaaba','kabah','الكعبة','البيت الحرام','بيت الله'),
        'SALAH-01':('salah','salat','prayer','الصلاة','صلاة'),
        'SEERAH-01':('seerah','sirah','السيرة'),
        'HISTORY-01':('islamic history','history','التاريخ الإسلامي','التاريخ الاسلامي','الأحزاب','البيعة'),
        'QURAN-01':('quran','qur’an','القرآن','قرآن','آية','الآية','verse'),
        'WUDU-01':('wudu','ablution','وضوء','الوضوء'),
        'ZAKAT-01':('zakat','الزكاة','زكاة'),
        'WAHY-01':('revelation','الوحي'),
        'HIJRAH-01':('hijrah','hijra','الهجرة'),
        'BADR-01':('badr','بدر'),
    }
    return any(term in q for term in topics.get(station_code,()))


class QuestionClassifierService:
    async def classify(self, question: str, station_context: bool = False) -> Classification:
        q = question.casefold()
        personal = ('my marriage', 'my divorce', 'my wife', 'my husband', 'am i sinful', 'personal fatwa', 'for me', 'in my case', 'my situation', 'my circumstances', 'in this situation', 'in my circumstances', 'my spouse', 'my partner', 'my relationship', 'what should i do', 'هل يجوز لي', 'زوجي', 'زوجتي', 'طلاق', 'فتوى شخصية', 'حلال لي', 'حرام علي', 'في حالتي', 'حالتي', 'ظروفي', 'ماذا يجب علي', 'فعلت كذا', 'هل علي إثم')
        sharia = ('is it permissible', 'is it halal', 'is it haram', 'ruling', 'fatwa', 'حكم شرعي', 'ما حكم', 'حكم البيع', 'هل يجوز', 'حلال', 'حرام')
        islamic = ('quran', 'hadith', 'prophet', 'islam', 'muslim', 'kaaba', 'tawhid', 'tawheed', 'scholar', 'consensus', 'tafsir', 'hijrah', 'hijra', 'migration to medina', 'the migration', 'badr', 'revelation', 'الوحي', 'بدر', 'السيرة', 'الهجرة', 'التاريخ الإسلامي', 'القرآن', 'حديث', 'النبي', 'الإسلام', 'المسلم', 'الكعبة', 'توحيد', 'العلماء', 'سورة', 'اتفق')
        matches = (
            (QuestionCategory.personal_fatwa, personal),
            (QuestionCategory.general_shariah_question, sharia),
            (QuestionCategory.islamic_knowledge, islamic),
            (QuestionCategory.general_knowledge, ('opening hours', 'where is', 'station', 'exhibition', 'museum', 'artifact', 'hours', 'مواعيد', 'أين', 'محطة', 'المعرض', 'المتحف')),
        )
        # Personal and legal questions keep priority. With station context,
        # generic educational wording should be classified before the generic
        # "station/exhibition" routing terms below.
        for category, rules in matches[:3]:
            matched = next((term for term in rules if term in q), None)
            if matched:
                # This is a deterministic, inspectable rule signal, not a calibrated probability.
                return Classification(category=category, matched_rule=matched, confidence=None, safe_fallback=False)
        if station_context and any(term in q for term in STATION_EDUCATIONAL_PROMPTS):
            return Classification(category=QuestionCategory.islamic_knowledge,
                matched_rule='station_educational_context', confidence=None, safe_fallback=False)
        if station_context and is_story_request(question):
            return Classification(category=QuestionCategory.islamic_knowledge,
                matched_rule='station_story_context', confidence=None, safe_fallback=False)
        category, rules = matches[3]
        matched = next((term for term in rules if term in q), None)
        if matched:
            return Classification(category=category, matched_rule=matched, confidence=None, safe_fallback=False)
        return Classification(category=QuestionCategory.unsupported_or_unclear, matched_rule=None,
                              confidence=None, safe_fallback=True)


class GovernanceEngine:
    def level_for(self, category: QuestionCategory) -> int:
        return {QuestionCategory.general_knowledge: 1, QuestionCategory.islamic_knowledge: 2, QuestionCategory.general_shariah_question: 3, QuestionCategory.personal_fatwa: 4, QuestionCategory.unsupported_or_unclear: 0}[category]

    def escalation(self, category: QuestionCategory) -> dict | None:
        if category == QuestionCategory.personal_fatwa:
            return {'escalation_required': True, 'reason': 'This question requires qualified human guidance.', 'recommended_action': 'refer_to_qualified_guide_or_mufti'}
        return None


class TrustedSourceRouter:
    def allowed(self, category: QuestionCategory, approved_sources: list[str] | None = None) -> tuple[list[str], list[str]]:
        if category == QuestionCategory.general_knowledge:
            return ['exhibition'], []
        if category == QuestionCategory.islamic_knowledge:
            return ['quran', 'quran_translation', 'tafsir', 'tafsir_translation', 'hadith', 'islamic_education'], []
        if category == QuestionCategory.general_shariah_question:
            # Fail closed until project owners explicitly approve exact recorded source values.
            return ['fatwa'], approved_sources or []
        return [], []


class CrowdingAnalyzer:
    """Estimate crowding from unresolved taps in the configured recent window."""
    async def station(self, session: AsyncSession, station_id: int) -> dict:
        row = (await session.execute(text("select count(*)::int from app.interactions where station_id=:station and duration_s is null and started_at >= now() - make_interval(mins => :mins)"), {'station': station_id, 'mins': settings.crowding_window_minutes})).scalar_one()
        return {'station_id': station_id, 'active_interactions': row, 'window_minutes': settings.crowding_window_minutes,
                'status': crowding_status(row,settings.crowding_high_active_interactions),
                'estimate': 'Derived from recent unresolved interactions; no physical occupancy sensor is connected.'}

    async def all_stations(self, session: AsyncSession) -> list[dict]:
        ids = (await session.execute(text('select id from app.stations order by id'))).scalars().all()
        return [await self.station(session, i) for i in ids]


class PresentationEngine:
    def choose(self, language: str, level: str, has_question: bool = False) -> str:
        if has_question or level == VisitorLevel.beginner:
            return 'short_text'
        if language in {'ar', 'en'}:
            return 'audio_guidance'
        return 'interactive_visual'


class RecommendationEngine:
    async def recommend(self, session: AsyncSession, card_id: str, current_station: int | None = None, language: str = 'en') -> dict:
        current_code=(await session.execute(text('select code from app.stations where id=:id'),{'id':current_station})).scalar_one_or_none() if current_station is not None else None
        pool=list(recommendation_station_pool(current_code))
        rows = (await session.execute(text("""with visitor_topics as (
              select s.topic,max(i.started_at) last_seen from app.interactions i
              join app.stations s on s.id=i.station_id where i.card_id=:card and s.topic is not null group by s.topic
            )
            select s.id,s.code,s.name,s.topic,
              count(i.id) filter(where i.duration_s is null and i.started_at >= now()-make_interval(mins=>:mins)) as active,
              exists(select 1 from visitor_topics t where t.topic=s.topic) as continues_topic
            from app.stations s left join app.interactions i on i.station_id=s.id
            where s.code=any(:pool) and (cast(:current as integer) is null or s.id<>:current)
              and not exists(select 1 from app.interactions seen where seen.card_id=:card and seen.station_id=s.id)
            group by s.id
            order by s.id"""), {'card': card_id, 'current': current_station, 'mins':settings.crowding_window_minutes,'pool':pool})).mappings().all()
        result=min(rows,key=lambda row:recommendation_rank(bool(row['continues_topic']),int(row['active']),row['id'])) if rows else None
        if not result:
            return {'recommended_station': None, 'reason': 'No additional station is currently available.'}
        if language=='ar':
            reason='هذه المحطة غير مزارة وتكمل موضوعًا استكشفته، وحركة الزوار فيها أقل.' if result['continues_topic'] else 'هذه محطة لم تزرها بعد وحركة الزوار فيها أقل.'
        else:
            reason='This unvisited station continues a topic you explored and currently has lower traffic.' if result['continues_topic'] else 'This station has not yet been visited and currently has lower traffic.'
        return {'recommended_station': result['code'], 'station_id': result['id'], 'name': result['name'], 'topic': result['topic'], 'reason': reason}


class JourneyReportService:
    async def build(self, session: AsyncSession, card_id: str) -> dict:
        visitor = (await session.execute(text("select lang,level from app.visitors where card_id=:card and (expires_at is null or expires_at>now())"), {'card': card_id})).mappings().first()
        if not visitor:
            raise VisitorNotFoundError('Unknown or expired visitor card')
        rows = (await session.execute(text("""select s.code,s.name,s.topic,i.started_at,i.duration_s from app.interactions i join app.stations s on s.id=i.station_id where i.card_id=:card order by i.started_at"""), {'card': card_id})).mappings().all()
        topics = list(dict.fromkeys(r['topic'] for r in rows if r['topic']))
        return {'card_id': card_id, 'language': visitor['lang'], 'level': visitor['level'], 'visited_stations': [dict(r) for r in rows], 'learning_summary': f"Visited {len(rows)} station interactions across {len(topics)} recorded topics.", 'knowledge_journey_score': min(100, len({r['code'] for r in rows}) * 20), 'topics_explored': topics, 'recommended_next_topics': [], 'interaction_statistics': {'interactions': len(rows), 'total_duration_seconds': sum(r['duration_s'] or 0 for r in rows)}}





def level3_sources_approved(requested: list[str], registry_rows: list[dict]) -> list[str]:
    """Only exact requested names with verified rights and explicit Level 3 approval pass."""
    eligible={row['source_name'] for row in registry_rows
        if row.get('rights_status')=='permitted'
        and row.get('verification_status')=='verified'
        and row.get('governance_level')=='APPROVED_LEVEL_3'}
    return sorted(set(requested) & eligible)

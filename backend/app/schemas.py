from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class VisitorLevel(StrEnum):
    beginner = 'beginner'
    intermediate = 'intermediate'
    advanced = 'advanced'


class QuestionCategory(StrEnum):
    general_knowledge = 'general_knowledge'
    islamic_knowledge = 'islamic_knowledge'
    general_shariah_question = 'general_shariah_question'
    personal_fatwa = 'personal_fatwa'
    unsupported_or_unclear = 'unsupported_or_unclear'


class Classification(BaseModel):
    category: QuestionCategory
    confidence: float | None = Field(default=None, ge=0, le=1)
    matched_rule: str | None = None
    safe_fallback: bool = False


class SourceCitation(BaseModel):
    title: str
    source: str
    reference: str | None = None
    url: str | None = None
    passage_id: str | None = None
    station_content_id: int | None = None
    content_type: str | None = None
    text: str | None = None
    surah: int | None = None
    ayah: int | None = None
    authenticity: str | None = None
    grade: str | None = None
    attribution: str | None = None
    rights_status: str | None = None
    verification_status: str | None = None
    governance_level: str | None = None


def visitor_citation(source: SourceCitation) -> dict[str, Any]:
    """Expose readable citation fields without internal database IDs or debug metadata."""
    data=source.model_dump(mode='json')
    return {
        'type': data.get('content_type'),
        'content_type': data.get('content_type'),
        'title': data.get('title'),
        'source': data.get('source'),
        'reference': data.get('reference'),
        'url': data.get('url'),
        'text': data.get('text'),
        'surah': data.get('surah'),
        'ayah': data.get('ayah'),
        'authenticity': data.get('authenticity'),
        'grade': data.get('grade'),
        'attribution': data.get('attribution'),
    }


class GeneratedAnswer(BaseModel):
    status: Literal['answered', 'insufficient_sources', 'referral', 'ai_unavailable'] = 'answered'
    answer: str | None
    sources: list[SourceCitation]
    confidence: float | None = Field(default=None, ge=0, le=1)
    ai_generated: bool = False
    reason: str | None = None
    escalation_required: bool = False
    recommended_action: str | None = None
    presentation_mode: str = 'text'
    recommended_station: str | None = None
    debug: dict[str, Any] | None = None


class StructuredAIAnswer(BaseModel):
    model_config = {'extra': 'forbid'}
    status: Literal['answered', 'insufficient_sources']
    answer: str | None
    used_sources: list[str]
    presentation_mode: Literal['text', 'storytelling', 'audio_guidance', 'interactive_visual'] = 'text'
    recommended_station: str | None = None

    @classmethod
    def validate_answer(cls, value):
        result = cls.model_validate(value)
        if result.status == 'answered' and not (result.answer or '').strip():
            raise ValueError('answered output must contain answer text')
        if result.status == 'insufficient_sources' and result.answer:
            raise ValueError('insufficient_sources output cannot include an answer')
        if result.status == 'insufficient_sources' and result.used_sources:
            raise ValueError('insufficient_sources output cannot cite sources')
        return result


class ClassifyRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class GenerateRequest(ClassifyRequest):
    card_id: str | None = Field(default=None, max_length=128)
    station_id: int | None = None
    language: str = Field(default='ar', min_length=2, max_length=12)
    level: VisitorLevel = VisitorLevel.beginner


class AskRequest(ClassifyRequest):
    card_id: str | None = Field(default=None, max_length=128)
    station_code: str | None = Field(default=None, max_length=64)
    interaction_id: int | None = None
    language: str | None = Field(default=None, min_length=2, max_length=12)
    level: VisitorLevel | None = None


class VisitorCreate(BaseModel):
    card_id: str | None = Field(default=None, min_length=1, max_length=128)
    lang: str = 'ar'
    level: VisitorLevel = VisitorLevel.beginner
    consent: bool


class TapRequest(BaseModel):
    card_id: str = Field(min_length=1, max_length=128)
    station_code: str = Field(min_length=1, max_length=64)
    request_id: str | None = Field(default=None, min_length=1, max_length=128)


class RFIDResolveRequest(BaseModel):
    rfid_uid: str = Field(min_length=1, max_length=64)


class RFIDAssignRequest(RFIDResolveRequest):
    card_id: str = Field(min_length=1, max_length=128)


class RFIDTapRequest(RFIDResolveRequest):
    station_code: str = Field(min_length=1, max_length=64)
    request_id: str | None = Field(default=None, min_length=1, max_length=128)


class StationOut(BaseModel):
    id: int
    code: str
    name: str
    topic: str | None = None
    location: str | None = None


class InteractRequest(BaseModel):
    card_id: str = Field(min_length=1, max_length=128)
    interaction_type: Literal['tap'] = 'tap'
    language: str | None = None
    request_id: str | None = Field(default=None, min_length=1, max_length=128)


class NFCInteractionRequest(InteractRequest):
    station_id: int


class InteractionOut(BaseModel):
    interaction_id: int
    station: StationOut
    content: dict[str, Any] | None
    presentation_mode: str
    crowding: dict[str, Any]
    recommended_station: dict[str, Any] | None


class RecommendationOut(BaseModel):
    recommended_station: str | None
    reason: str


class JourneyReport(BaseModel):
    card_id: str
    language: str
    level: VisitorLevel
    visited_stations: list[dict[str, Any]]
    learning_summary: str
    knowledge_journey_score: int
    topics_explored: list[str]
    recommended_next_topics: list[str]
    interaction_statistics: dict[str, Any]


class HealthOut(BaseModel):
    status: str
    database: str
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_configured: bool = False


import asyncio

from app.services import QuestionClassifierService
from app.storytelling import is_story_request
from app.schemas import QuestionCategory, StructuredAIAnswer


def test_story_intent_detects_english_and_arabic_narrative_phrases():
    assert is_story_request("Tell me the story of the Battle of Badr.")
    assert is_story_request("What happened here?")
    assert is_story_request("احكِ لي قصة غزوة بدر بطريقة بسيطة وممتعة.")
    assert is_story_request("وش صار في غزوة بدر؟")


def test_station_context_turns_generic_story_question_into_trusted_knowledge_retrieval():
    classifier = QuestionClassifierService()
    without_station = asyncio.run(classifier.classify("What happened here?"))
    with_station = asyncio.run(classifier.classify("What happened here?", station_context=True))
    assert without_station.category == QuestionCategory.unsupported_or_unclear
    assert with_station.category == QuestionCategory.islamic_knowledge
    assert with_station.safe_fallback is False


def test_story_mode_does_not_override_personal_fatwa_classification():
    result = asyncio.run(QuestionClassifierService().classify(
        "Tell me a story about my divorce; what should I do?", station_context=True))
    assert result.category == QuestionCategory.personal_fatwa


def test_storytelling_presentation_mode_is_part_of_strict_provider_contract():
    result = StructuredAIAnswer.validate_answer({
        "status": "answered", "answer": "A sourced narrative.",
        "used_sources": ["trusted-source"], "presentation_mode": "storytelling",
        "recommended_station": None,
    })
    assert result.presentation_mode == "storytelling"

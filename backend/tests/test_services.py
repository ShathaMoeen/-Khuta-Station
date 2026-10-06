from app.schemas import QuestionCategory
from app.services import GovernanceEngine, PresentationEngine, QuestionClassifierService


def test_personal_fatwa_escalates_without_answer():
    result = GovernanceEngine().escalation(QuestionCategory.personal_fatwa)
    assert result and result['escalation_required'] is True
    assert result['recommended_action'] == 'refer_to_qualified_guide_or_mufti'


def test_classifier_flags_personal_fatwa():
    import asyncio
    result = asyncio.run(QuestionClassifierService().classify('Can you give a personal fatwa for me about my marriage?'))
    assert result.category == QuestionCategory.personal_fatwa
    assert result.confidence is None
    assert result.matched_rule == 'my marriage'


def test_uncertain_question_fails_closed():
    import asyncio
    result = asyncio.run(QuestionClassifierService().classify('Can you explain this?'))
    assert result.safe_fallback is True
    assert result.category == QuestionCategory.unsupported_or_unclear


def test_source_router_has_no_personal_fatwa_sources():
    from app.services import TrustedSourceRouter
    assert TrustedSourceRouter().allowed(QuestionCategory.personal_fatwa) == ([], [])


def test_presentation_mode_is_typed_output():
    assert PresentationEngine().choose('en', 'advanced') == 'audio_guidance'
    assert PresentationEngine().choose('ur', 'advanced') == 'interactive_visual'


def test_governance_levels_are_explicit():
    engine=GovernanceEngine()
    assert engine.level_for(QuestionCategory.general_knowledge)==1
    assert engine.level_for(QuestionCategory.islamic_knowledge)==2
    assert engine.level_for(QuestionCategory.general_shariah_question)==3
    assert engine.level_for(QuestionCategory.personal_fatwa)==4


def test_unrecognized_questions_fall_back_to_human_review():
    import asyncio
    result=asyncio.run(QuestionClassifierService().classify('Please help me decide what to do.'))
    assert result.safe_fallback



def test_hijrah_is_classified_as_islamic_knowledge():
    import asyncio
    result = asyncio.run(QuestionClassifierService().classify('What is the significance of the Hijrah?'))
    assert result.category == QuestionCategory.islamic_knowledge


def test_personal_spouse_situation_escalates():
    import asyncio
    result = asyncio.run(QuestionClassifierService().classify('Can I divorce my spouse in this situation?'))
    assert result.category == QuestionCategory.personal_fatwa
    assert GovernanceEngine().escalation(result.category)['escalation_required'] is True


def test_arabic_personal_ruling_is_referred_without_probability_claim():
    import asyncio
    result=asyncio.run(QuestionClassifierService().classify('أنا في دولة كذا، هل يجوز لي فعل كذا في زواجي؟'))
    assert result.category==QuestionCategory.personal_fatwa
    assert result.matched_rule=='هل يجوز لي'
    assert result.confidence is None


def test_tawhid_question_is_classified_as_islamic_knowledge():
    import asyncio
    result=asyncio.run(QuestionClassifierService().classify('What does Tawhid mean?'))
    assert result.category==QuestionCategory.islamic_knowledge
from app.schemas import QuestionCategory
from app.services import level3_sources_approved


def test_unverified_sources_cannot_unlock_level_three():
    requested=['source A']
    rows=[{'source_name':'source A','rights_status':'needs_review','verification_status':'unverified','governance_level':'UNVERIFIED'}]
    assert level3_sources_approved(requested,rows)==[]


def test_level_three_requires_all_explicit_approval_fields():
    requested=['source A','source B']
    rows=[
        {'source_name':'source A','rights_status':'permitted','verification_status':'verified','governance_level':'APPROVED_LEVEL_3'},
        {'source_name':'source B','rights_status':'permitted','verification_status':'reviewed','governance_level':'APPROVED_LEVEL_3'},
    ]
    assert level3_sources_approved(requested,rows)==['source A']


def test_unrequested_approved_source_stays_out_of_allowlist():
    rows=[{'source_name':'source A','rights_status':'permitted','verification_status':'verified','governance_level':'APPROVED_LEVEL_3'}]
    assert level3_sources_approved(['other'],rows)==[]

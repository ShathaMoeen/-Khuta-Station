from app.core.config import get_settings


def test_settings_use_environment_configuration(monkeypatch):
    monkeypatch.setenv('DATABASE_URL','postgresql://db.example/islamic')
    monkeypatch.setenv('EMBEDDING_PROVIDER','openai')
    monkeypatch.setenv('EMBEDDING_MODEL','text-embedding-3-small')
    get_settings.cache_clear()
    try:
        settings=get_settings()
        assert settings.database_url=='postgresql+asyncpg://db.example/islamic'
        assert settings.embedding_provider=='openai'
        assert settings.embedding_model=='text-embedding-3-small'
        assert settings.openai_embedding_model=='text-embedding-3-small'
    finally:
        get_settings.cache_clear()


def test_gemini_configuration_uses_generic_provider_models(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY','test-only-placeholder')
    monkeypatch.setenv('LLM_PROVIDER','gemini')
    monkeypatch.setenv('LLM_MODEL','gemini-test-model')
    monkeypatch.setenv('EMBEDDING_PROVIDER','gemini')
    monkeypatch.setenv('EMBEDDING_MODEL','gemini-embedding-2')
    monkeypatch.setenv('EMBEDDING_DIMENSIONS','1536')
    get_settings.cache_clear()
    try:
        settings=get_settings()
        assert settings.llm_provider=='gemini'
        assert settings.llm_model=='gemini-test-model'
        assert settings.embedding_provider=='gemini'
        assert settings.embedding_model=='gemini-embedding-2'
        assert settings.ai_provider_configured is True
    finally:
        get_settings.cache_clear()

from functools import lru_cache
import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

@dataclass
class Settings:
    database_url: str | None = None
    app_env: str = 'development'
    app_name: str = 'KHUTA API'
    api_prefix: str = ''
    cors_origins: list[str] = field(default_factory=lambda: ['http://localhost:3000'])
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    llm_provider: str = 'openai'
    llm_model: str = 'gpt-4o-mini'
    openai_model: str = 'gpt-4o-mini'
    openai_embedding_model: str = 'text-embedding-3-small'
    embedding_provider: str = 'openai'
    embedding_model: str = 'text-embedding-3-small'
    embedding_dimensions: int = 1536
    pgvector_enabled: bool = True
    classification_confidence_threshold: float = 0.72
    crowding_window_minutes: int = 5
    crowding_high_active_interactions: int = 8
    approved_shariah_sources: list[str] = field(default_factory=list)
    admin_api_key: str | None = None
    device_api_key: str | None = None
    log_level: str = 'INFO'
    rate_limit_per_minute: int = 60

    @property
    def llm_api_key(self) -> str | None:
        return self.gemini_api_key if self.llm_provider=='gemini' else self.openai_api_key if self.llm_provider=='openai' else None

    @property
    def ai_provider_configured(self) -> bool:
        return self.llm_provider==self.embedding_provider and bool(self.llm_api_key)

    def __post_init__(self):
        if self.embedding_dimensions != 1536:
            raise ValueError('This migration uses 1536-dimensional vectors; change the migration before configuring a different size.')


@lru_cache
def get_settings() -> Settings:
    backend_env=Path(__file__).resolve().parents[2]/'.env'
    load_dotenv(backend_env, override=False)
    load_dotenv(Path('.env'), override=False)
    source=os.environ
    def val(key, default): return source.get(key, default)
    def csv(key, default): return [x.strip() for x in val(key, default).split(',') if x.strip()]
    database=(val('DATABASE_URL','') or '').strip() or None
    if database and database.startswith('postgresql://'): database=database.replace('postgresql://','postgresql+asyncpg://',1)
    return Settings(database_url=database, app_env=val('APP_ENV','development'), app_name=val('APP_NAME','KHUTA API'),
        api_prefix=val('API_PREFIX',''), cors_origins=csv('CORS_ORIGINS','http://localhost:3000'),
        openai_api_key=val('OPENAI_API_KEY','') or None,
        gemini_api_key=val('GEMINI_API_KEY',val('GOOGLE_API_KEY','')) or None,
        llm_provider=val('LLM_PROVIDER','openai').lower(),
        llm_model=val('LLM_MODEL',val('OPENAI_MODEL','gpt-4o-mini')),
        openai_model=val('LLM_MODEL',val('OPENAI_MODEL','gpt-4o-mini')),
        openai_embedding_model=val('EMBEDDING_MODEL',val('OPENAI_EMBEDDING_MODEL','text-embedding-3-small')),
        embedding_provider=val('EMBEDDING_PROVIDER','openai').lower(),
        embedding_model=val('EMBEDDING_MODEL',val('OPENAI_EMBEDDING_MODEL','text-embedding-3-small')),
        embedding_dimensions=int(val('EMBEDDING_DIMENSIONS','1536')), pgvector_enabled=val('PGVECTOR_ENABLED','true').lower()=='true',
        classification_confidence_threshold=float(val('CLASSIFICATION_CONFIDENCE_THRESHOLD','0.72')),
        crowding_window_minutes=int(val('CROWDING_WINDOW_MINUTES','5')),
        crowding_high_active_interactions=int(val('CROWDING_HIGH_ACTIVE_INTERACTIONS','8')),
        approved_shariah_sources=csv('APPROVED_SHARIAH_SOURCES',''), admin_api_key=val('ADMIN_API_KEY','') or None,
        device_api_key=val('DEVICE_API_KEY','') or None,
        log_level=val('LOG_LEVEL','INFO'), rate_limit_per_minute=int(val('RATE_LIMIT_PER_MINUTE','60')))


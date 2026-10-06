"""SQLAlchemy mappings for the inspected tables. Application startup never calls create_all."""
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Identity, Index, Integer, Numeric, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

EMBEDDING_DIMENSIONS = 1536


class Base(DeclarativeBase):
    pass


class Visitor(Base):
    __tablename__ = 'visitors'
    __table_args__ = (CheckConstraint("level in ('beginner','intermediate','advanced')", name='chk_visitors_level'), {'schema': 'app'})

    card_id: Mapped[str] = mapped_column(Text, primary_key=True)
    lang: Mapped[str] = mapped_column(Text, nullable=False, server_default='ar')
    level: Mapped[str] = mapped_column(Text, nullable=False, server_default='beginner')
    consent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    interactions: Mapped[list['Interaction']] = relationship(back_populates='visitor')


class Station(Base):
    __tablename__ = 'stations'
    __table_args__ = {'schema': 'app'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content: Mapped[list['StationContent']] = relationship(back_populates='station')
    interactions: Mapped[list['Interaction']] = relationship(back_populates='station')


class StationContent(Base):
    __tablename__ = 'station_content'
    __table_args__ = (CheckConstraint("level in ('beginner','intermediate','advanced')", name='chk_station_content_level'), {'schema': 'app'})

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey('app.stations.id', ondelete='CASCADE'), nullable=False)
    lang: Mapped[str] = mapped_column(Text, nullable=False, server_default='ar')
    level: Mapped[str] = mapped_column(Text, nullable=False, server_default='beginner')
    title: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    source_note: Mapped[str | None] = mapped_column(Text)
    station: Mapped[Station] = relationship(back_populates='content')


class Interaction(Base):
    __tablename__ = 'interactions'
    __table_args__ = (Index('idx_interactions_card', 'card_id'), Index('ix_interactions_station_started', 'station_id', 'started_at'), {'schema': 'app'})

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    card_id: Mapped[str] = mapped_column(ForeignKey('app.visitors.card_id', ondelete='CASCADE'), nullable=False)
    station_id: Mapped[int] = mapped_column(ForeignKey('app.stations.id'), nullable=False)
    request_id: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_s: Mapped[int | None] = mapped_column(Integer)
    visitor: Mapped[Visitor] = relationship(back_populates='interactions')
    station: Mapped[Station] = relationship(back_populates='interactions')
    generated_content: Mapped[list['GeneratedContent']] = relationship(back_populates='interaction')


class GeneratedContent(Base):
    __tablename__ = 'generated_content'
    __table_args__ = {'schema': 'app'}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    interaction_id: Mapped[int] = mapped_column(ForeignKey('app.interactions.id', ondelete='CASCADE'), nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    lang: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Any | None] = mapped_column(JSONB)
    model: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    interaction: Mapped[Interaction] = relationship(back_populates='generated_content')


class Passage(Base):
    __tablename__ = 'passages'
    __table_args__ = {'schema': 'public'}

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    lang: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[str | None] = mapped_column(Text)
    surah: Mapped[int | None] = mapped_column(Integer)
    ayah: Mapped[int | None] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_norm: Mapped[str] = mapped_column(Text, nullable=False)
    authenticity: Mapped[str | None] = mapped_column(Text)
    grade: Mapped[str | None] = mapped_column(Text)
    translation_of_type: Mapped[str | None] = mapped_column(Text)
    translation_of_book_id: Mapped[int | None] = mapped_column(Integer)
    attribution: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    char_len: Mapped[int | None] = mapped_column(Integer)
    meta: Mapped[dict[str, Any] | None] = mapped_column('meta', JSONB)
    level: Mapped[str | None] = mapped_column(Text)


class ContentSource(Base):
    __tablename__ = 'content_sources'
    __table_args__ = {'schema': 'app'}

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    source_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    attribution: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column('metadata', JSONB)
    publisher: Mapped[str | None] = mapped_column(Text)
    license: Mapped[str | None] = mapped_column(Text)
    license_url: Mapped[str | None] = mapped_column(Text)
    rights_status: Mapped[str] = mapped_column(Text, nullable=False, server_default='needs_review')
    verification_status: Mapped[str] = mapped_column(Text, nullable=False, server_default='unverified')
    governance_level: Mapped[str] = mapped_column(Text, nullable=False, server_default='UNVERIFIED')
    attribution_required: Mapped[bool | None] = mapped_column(Boolean)
    attribution_text: Mapped[str | None] = mapped_column(Text)
    verification_evidence_url: Mapped[str | None] = mapped_column(Text)
    source_version: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewer: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StationPassage(Base):
    __tablename__ = 'station_passages'
    __table_args__ = (UniqueConstraint('station_id','passage_id','relationship_type',name='uq_station_passages_link'), {'schema':'app'})
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey('app.stations.id', ondelete='CASCADE'), nullable=False)
    passage_id: Mapped[str] = mapped_column(ForeignKey('public.passages.id', ondelete='RESTRICT'), nullable=False)
    relationship_type: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[float | None] = mapped_column(Numeric(5,4))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StationContentProvenance(Base):
    __tablename__ = 'station_content_provenance'
    __table_args__ = (UniqueConstraint('station_content_id','source_id','reference',name='uq_station_content_provenance'), {'schema':'app'})
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    station_content_id: Mapped[int] = mapped_column(ForeignKey('app.station_content.id', ondelete='CASCADE'), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey('app.content_sources.id', ondelete='RESTRICT'), nullable=False)
    passage_id: Mapped[str | None] = mapped_column(ForeignKey('public.passages.id', ondelete='RESTRICT'))
    reference: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(Text, nullable=False, server_default='unverified')
    rights_status: Mapped[str] = mapped_column(Text, nullable=False, server_default='needs_review')
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class MediaAsset(Base):
    __tablename__ = 'media_assets'
    __table_args__ = (
        CheckConstraint("rights_status in ('permitted','needs_review','restricted')", name='ck_media_assets_rights'),
        CheckConstraint("verification_status in ('verified','reviewed','unverified')", name='ck_media_assets_verification'),
        Index('ix_media_assets_station_approved', 'station_id', 'verification_status', 'rights_status'),
        {'schema': 'app'},
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey('app.stations.id', ondelete='CASCADE'), nullable=False)
    media_type: Mapped[str] = mapped_column(Text, nullable=False)
    title_ar: Mapped[str | None] = mapped_column(Text)
    title_en: Mapped[str | None] = mapped_column(Text)
    caption_ar: Mapped[str | None] = mapped_column(Text)
    caption_en: Mapped[str | None] = mapped_column(Text)
    asset_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    institution: Mapped[str | None] = mapped_column(Text)
    creator: Mapped[str | None] = mapped_column(Text)
    license: Mapped[str | None] = mapped_column(Text)
    license_url: Mapped[str | None] = mapped_column(Text)
    rights_status: Mapped[str] = mapped_column(Text, nullable=False, server_default='needs_review')
    verification_status: Mapped[str] = mapped_column(Text, nullable=False, server_default='unverified')
    attribution_text: Mapped[str | None] = mapped_column(Text)
    alt_text_ar: Mapped[str | None] = mapped_column(Text)
    alt_text_en: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[Any | None] = mapped_column('metadata', JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Embedding(Base):
    __tablename__ = 'embeddings'
    __table_args__ = (
        UniqueConstraint('content_id', 'chunk_index', name='uq_embeddings_content_chunk'),
        CheckConstraint("visitor_level is null or visitor_level in ('all','beginner','intermediate','advanced')", name='ck_embeddings_visitor_level'),
        Index('ix_embeddings_language_type_level', 'language', 'content_type', 'visitor_level'),
        Index('ix_embeddings_source', 'source_id'),
        {'schema': 'app'},
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    content_id: Mapped[str] = mapped_column(ForeignKey('public.passages.id', ondelete='CASCADE'), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey('app.content_sources.id', ondelete='RESTRICT'), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    language: Mapped[str] = mapped_column(Text, nullable=False)
    visitor_level: Mapped[str | None] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column('metadata', JSONB)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


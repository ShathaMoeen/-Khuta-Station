"""Add source registry and pgvector embeddings without changing existing records.

Revision ID: 0001_additive_rag_storage
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

revision = '0001_additive_rag_storage'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # The vector extension already exists on the inspected PostgreSQL instance.
    op.execute('CREATE SCHEMA IF NOT EXISTS app')
    op.create_table(
        'content_sources',
        sa.Column('id', sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column('source_key', sa.Text(), nullable=False, unique=True),
        sa.Column('source_name', sa.Text(), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('attribution', sa.Text()),
        sa.Column('source_url', sa.Text()),
        sa.Column('metadata', JSONB()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='app',
    )
    op.create_table(
        'embeddings',
        sa.Column('id', sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column('content_id', sa.Text(), sa.ForeignKey('public.passages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_id', sa.BigInteger(), sa.ForeignKey('app.content_sources.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('language', sa.Text(), nullable=False),
        sa.Column('visitor_level', sa.Text()),
        sa.Column('content_type', sa.Text(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('reference', sa.Text()),
        sa.Column('metadata', JSONB()),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('content_id', 'chunk_index', name='uq_embeddings_content_chunk'),
        sa.CheckConstraint("visitor_level is null or visitor_level in ('all','beginner','intermediate','advanced')", name='ck_embeddings_visitor_level'),
        schema='app',
    )
    op.create_index('ix_embeddings_language_type_level', 'embeddings', ['language', 'content_type', 'visitor_level'], schema='app')
    op.create_index('ix_embeddings_source', 'embeddings', ['source_id'], schema='app')
    op.execute('CREATE INDEX ix_embeddings_vector_hnsw ON app.embeddings USING hnsw (embedding vector_cosine_ops)')
    op.create_index('ix_interactions_station_started', 'interactions', ['station_id', 'started_at'], schema='app')


def downgrade():
    # Explicit downgrade is reversible and only drops objects created by this migration.
    op.drop_index('ix_interactions_station_started', table_name='interactions', schema='app')
    op.drop_table('embeddings', schema='app')
    op.drop_table('content_sources', schema='app')


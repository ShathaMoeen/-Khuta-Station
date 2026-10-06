"""Add station media registry and optional tap idempotency keys.

Revision ID: 0004_media_request_key
Revises: 0003_passage_provenance
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0004_media_request_key'
down_revision = '0003_passage_provenance'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('interactions', sa.Column('request_id', sa.Text(), nullable=True), schema='app')
    op.create_index('uq_interactions_request_id', 'interactions', ['request_id'], unique=True,
                    postgresql_where=sa.text('request_id is not null'), schema='app')
    op.create_table(
        'media_assets',
        sa.Column('id', sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column('station_id', sa.Integer(), sa.ForeignKey('app.stations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('media_type', sa.Text(), nullable=False),
        sa.Column('title_ar', sa.Text()),
        sa.Column('title_en', sa.Text()),
        sa.Column('caption_ar', sa.Text()),
        sa.Column('caption_en', sa.Text()),
        sa.Column('asset_url', sa.Text(), nullable=False),
        sa.Column('thumbnail_url', sa.Text()),
        sa.Column('source_url', sa.Text()),
        sa.Column('institution', sa.Text()),
        sa.Column('creator', sa.Text()),
        sa.Column('license', sa.Text()),
        sa.Column('license_url', sa.Text()),
        sa.Column('rights_status', sa.Text(), nullable=False, server_default='needs_review'),
        sa.Column('verification_status', sa.Text(), nullable=False, server_default='unverified'),
        sa.Column('attribution_text', sa.Text()),
        sa.Column('alt_text_ar', sa.Text()),
        sa.Column('alt_text_en', sa.Text()),
        sa.Column('metadata', JSONB()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rights_status in ('permitted','needs_review','restricted')", name='ck_media_assets_rights'),
        sa.CheckConstraint("verification_status in ('verified','reviewed','unverified')", name='ck_media_assets_verification'),
        schema='app',
    )
    op.create_index('ix_media_assets_station_approved', 'media_assets',
                    ['station_id', 'verification_status', 'rights_status'], schema='app')


def downgrade():
    op.drop_index('ix_media_assets_station_approved', table_name='media_assets', schema='app')
    op.drop_table('media_assets', schema='app')
    op.drop_index('uq_interactions_request_id', table_name='interactions', schema='app')
    op.drop_column('interactions', 'request_id', schema='app')

"""Add an optional exact local passage link to station content provenance.

Revision ID: 0003_passage_provenance
Revises: 0002_source_governance_demo
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_passage_provenance'
down_revision = '0002_source_governance_demo'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'station_content_provenance',
        sa.Column('passage_id', sa.Text(), sa.ForeignKey('public.passages.id', ondelete='RESTRICT'), nullable=True),
        schema='app',
    )
    op.create_index('ix_station_content_provenance_passage', 'station_content_provenance', ['passage_id'], schema='app')


def downgrade():
    op.drop_index('ix_station_content_provenance_passage', table_name='station_content_provenance', schema='app')
    op.drop_column('station_content_provenance', 'passage_id', schema='app')

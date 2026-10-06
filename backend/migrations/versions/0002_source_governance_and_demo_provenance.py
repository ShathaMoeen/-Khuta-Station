"""Add source governance, station-to-passage links, and demo provenance.
Revision ID: 0002_source_governance_demo
Revises: 0001_additive_rag_storage
"""
from alembic import op
import sqlalchemy as sa
revision = '0002_source_governance_demo'
down_revision = '0001_additive_rag_storage'
branch_labels = None
depends_on = None

def upgrade():
    fields = [('publisher',sa.Text()),('license',sa.Text()),('license_url',sa.Text()),('rights_status',sa.Text(),'needs_review'),('verification_status',sa.Text(),'unverified'),('governance_level',sa.Text(),'UNVERIFIED'),('attribution_required',sa.Boolean()),('attribution_text',sa.Text()),('verification_evidence_url',sa.Text()),('source_version',sa.Text()),('retrieved_at',sa.DateTime(timezone=True)),('verified_at',sa.DateTime(timezone=True)),('reviewer',sa.Text()),('notes',sa.Text())]
    for field in fields:
        name, typ, *default = field
        kwargs = {'nullable':False,'server_default':default[0]} if default else {}
        op.add_column('content_sources',sa.Column(name,typ,**kwargs),schema='app')
    op.create_check_constraint('ck_content_sources_rights_status','content_sources',"rights_status in ('unknown','needs_review','permitted','restricted')",schema='app')
    op.create_check_constraint('ck_content_sources_verification_status','content_sources',"verification_status in ('unverified','reviewed','verified')",schema='app')
    op.create_check_constraint('ck_content_sources_governance_level','content_sources',"governance_level in ('UNVERIFIED','REVIEWED','APPROVED_LEVEL_1','APPROVED_LEVEL_2','APPROVED_LEVEL_3')",schema='app')
    op.create_table('station_passages',sa.Column('id',sa.BigInteger(),sa.Identity(),primary_key=True),sa.Column('station_id',sa.Integer(),sa.ForeignKey('app.stations.id',ondelete='CASCADE'),nullable=False),sa.Column('passage_id',sa.Text(),sa.ForeignKey('public.passages.id',ondelete='RESTRICT'),nullable=False),sa.Column('relationship_type',sa.Text(),nullable=False),sa.Column('priority',sa.Numeric(5,4)),sa.Column('notes',sa.Text()),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.UniqueConstraint('station_id','passage_id','relationship_type',name='uq_station_passages_link'),sa.CheckConstraint('priority is null or (priority >= 0 and priority <= 1)',name='ck_station_passages_priority'),schema='app')
    op.create_index('ix_station_passages_station','station_passages',['station_id'],schema='app')
    op.create_index('ix_station_passages_passage','station_passages',['passage_id'],schema='app')
    op.create_table('station_content_provenance',sa.Column('id',sa.BigInteger(),sa.Identity(),primary_key=True),sa.Column('station_content_id',sa.Integer(),sa.ForeignKey('app.station_content.id',ondelete='CASCADE'),nullable=False),sa.Column('source_id',sa.BigInteger(),sa.ForeignKey('app.content_sources.id',ondelete='RESTRICT'),nullable=False),sa.Column('reference',sa.Text()),sa.Column('source_url',sa.Text()),sa.Column('verification_status',sa.Text(),nullable=False,server_default='unverified'),sa.Column('rights_status',sa.Text(),nullable=False,server_default='needs_review'),sa.Column('retrieved_at',sa.DateTime(timezone=True)),sa.Column('notes',sa.Text()),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.UniqueConstraint('station_content_id','source_id','reference',name='uq_station_content_provenance'),sa.CheckConstraint("verification_status in ('unverified','reviewed','verified')",name='ck_station_content_provenance_verification'),sa.CheckConstraint("rights_status in ('unknown','needs_review','permitted','restricted')",name='ck_station_content_provenance_rights'),schema='app')

def downgrade():
    op.drop_table('station_content_provenance',schema='app')
    op.drop_index('ix_station_passages_passage',table_name='station_passages',schema='app')
    op.drop_index('ix_station_passages_station',table_name='station_passages',schema='app')
    op.drop_table('station_passages',schema='app')
    for name in ('ck_content_sources_governance_level','ck_content_sources_verification_status','ck_content_sources_rights_status'): op.drop_constraint(name,'content_sources',schema='app')
    for column in ('notes','reviewer','verified_at','retrieved_at','source_version','verification_evidence_url','attribution_text','attribution_required','governance_level','verification_status','rights_status','license_url','license','publisher'): op.drop_column('content_sources',column,schema='app')

"""create projects and requirements tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.Text, nullable=False),
        sa.Column('status', sa.Text, nullable=False, server_default='DRAFT'),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=datetime.utcnow),
    )
    op.create_index('ix_projects_status', 'projects', ['status'])
    op.create_index('ix_projects_created_by', 'projects', ['created_by'])

    # Requirements table
    op.create_table(
        'requirements',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.Text, nullable=False),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('data', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=datetime.utcnow),
    )
    op.create_unique_constraint('uq_requirements_project_code', 'requirements', ['project_id', 'code'])
    op.create_index('ix_requirements_project_version', 'requirements', ['project_id', 'version'])
    op.execute('CREATE INDEX ix_requirements_data_gin ON requirements USING GIN (data)')

    # Requirements versions table (audit trail)
    op.create_table(
        'requirements_versions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('requirement_id', UUID(as_uuid=True), sa.ForeignKey('requirements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('data', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_unique_constraint('uq_requirements_versions_req_version', 'requirements_versions', ['requirement_id', 'version'])
    op.create_index('ix_requirements_versions_requirement_id', 'requirements_versions', ['requirement_id'])
    op.execute('CREATE INDEX ix_requirements_versions_data_gin ON requirements_versions USING GIN (data)')


def downgrade() -> None:
    op.drop_table('requirements_versions')
    op.drop_table('requirements')
    op.drop_table('projects')

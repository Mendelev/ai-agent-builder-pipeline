"""create qa_sessions table

Revision ID: 002
Revises: 001
Create Date: 2025-10-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.types import UUID as CustomUUID, JSONB as CustomJSONB

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create qa_sessions table
    op.create_table(
        'qa_sessions',
        sa.Column('id', CustomUUID(), primary_key=True),
        sa.Column('project_id', CustomUUID(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('request_id', sa.String(36), nullable=False, unique=True),
        sa.Column('round', sa.Integer, nullable=False, default=1),
        sa.Column('questions', CustomJSONB(), nullable=False),
        sa.Column('answers', CustomJSONB(), nullable=True),
        sa.Column('quality_flags', CustomJSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create indexes for performance
    op.create_index('ix_qa_sessions_project_id', 'qa_sessions', ['project_id'])
    op.create_index('ix_qa_sessions_request_id', 'qa_sessions', ['request_id'])
    op.create_index('ix_qa_sessions_project_round', 'qa_sessions', ['project_id', 'round'])
    
    # Add requirements_version to projects table
    op.add_column('projects', sa.Column('requirements_version', sa.Integer, nullable=False, server_default='1'))
    op.create_index('ix_projects_requirements_version', 'projects', ['requirements_version'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_projects_requirements_version', 'projects')
    op.drop_index('ix_qa_sessions_project_round', 'qa_sessions')
    op.drop_index('ix_qa_sessions_request_id', 'qa_sessions')
    op.drop_index('ix_qa_sessions_project_id', 'qa_sessions')
    
    # Drop column
    op.drop_column('projects', 'requirements_version')
    
    # Drop table
    op.drop_table('qa_sessions')

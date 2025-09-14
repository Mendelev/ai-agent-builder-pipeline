# backend/migrations/versions/001_create_requirements_tables.py
"""Create requirements tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create enum type
    op.execute("CREATE TYPE projectstatus AS ENUM ('DRAFT', 'REQS_READY', 'DESIGN_READY', 'APPROVED', 'IN_PROGRESS', 'COMPLETED')")
    
    # Create projects table
    op.create_table('projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('DRAFT', 'REQS_READY', 'DESIGN_READY', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', name='projectstatus', create_type=False), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create requirements table with constraints
    op.create_table('requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('acceptance_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('dependencies', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('is_coherent', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')", name='check_priority'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique index for project_id + key
    op.create_index('idx_project_key', 'requirements', ['project_id', 'key'], unique=True)
    
    # Create GIN index for JSONB search
    op.create_index('idx_acceptance_criteria_gin', 'requirements', ['acceptance_criteria'], unique=False, postgresql_using='gin')
    
    # Create requirement_iterations table
    op.create_table('requirement_iterations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['requirement_id'], ['requirements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_requirement_version', 'requirement_iterations', ['requirement_id', 'version'], unique=True)
    
    # Create requirement_questions table
    op.create_table('requirement_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('answered_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['requirement_id'], ['requirements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for faster queries
    op.create_index('idx_requirement_questions', 'requirement_questions', ['requirement_id', 'is_resolved'])

def downgrade() -> None:
    op.drop_index('idx_requirement_questions', table_name='requirement_questions')
    op.drop_table('requirement_questions')
    op.drop_index('idx_requirement_version', table_name='requirement_iterations')
    op.drop_table('requirement_iterations')
    op.drop_index('idx_acceptance_criteria_gin', table_name='requirements')
    op.drop_index('idx_project_key', table_name='requirements')
    op.drop_table('requirements')
    op.drop_table('projects')
    op.execute('DROP TYPE projectstatus')
# backend/migrations/versions/002_create_plan_tables.py
"""Create plan tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create plan status enum
    op.execute("CREATE TYPE planstatus AS ENUM ('DRAFT', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')")
    
    # Create plans table
    op.create_table('plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('DRAFT', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='planstatus', create_type=False), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('use_code', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('include_checklist', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('constraints', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('total_duration_days', sa.Float(), nullable=True, server_default='0'),
        sa.Column('risk_score', sa.Float(), nullable=True, server_default='0'),
        sa.Column('coverage_percentage', sa.Float(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for quick lookup
    op.create_index('idx_project_version', 'plans', ['project_id', 'version'], unique=True)
    op.create_index('idx_project_latest', 'plans', ['project_id', 'created_at'])
    
    # Create plan_phases table
    op.create_table('plan_phases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phase_id', sa.String(length=20), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('objective', sa.Text(), nullable=False),
        sa.Column('deliverables', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('activities', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('dependencies', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('estimated_days', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=True, server_default='medium'),
        sa.Column('risks', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('requirements_covered', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('definition_of_done', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('resources_required', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("risk_level IN ('low', 'medium', 'high', 'critical')", name='check_risk_level'),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_plan_phase', 'plan_phases', ['plan_id', 'phase_id'], unique=True)
    op.create_index('idx_phase_sequence', 'plan_phases', ['plan_id', 'sequence'])

def downgrade() -> None:
    op.drop_index('idx_phase_sequence', table_name='plan_phases')
    op.drop_index('idx_plan_phase', table_name='plan_phases')
    op.drop_table('plan_phases')
    op.drop_index('idx_project_latest', table_name='plans')
    op.drop_index('idx_project_version', table_name='plans')
    op.drop_table('plans')
    op.execute('DROP TYPE planstatus')
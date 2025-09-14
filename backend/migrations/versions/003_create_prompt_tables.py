# backend/migrations/versions/003_create_prompt_tables.py
"""Create prompt tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create prompt_bundles table
    op.create_table('prompt_bundles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('include_code', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('context_md', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('total_prompts', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_bundle_project', 'prompt_bundles', ['project_id', 'created_at'])
    op.create_index('idx_bundle_plan', 'prompt_bundles', ['plan_id'])
    
    # Create prompt_items table
    op.create_table('prompt_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bundle_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phase_id', sa.String(length=20), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content_md', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['bundle_id'], ['prompt_bundles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_prompt_bundle_phase', 'prompt_items', ['bundle_id', 'phase_id'], unique=True)
    op.create_index('idx_prompt_sequence', 'prompt_items', ['bundle_id', 'sequence'])

def downgrade() -> None:
    op.drop_index('idx_prompt_sequence', table_name='prompt_items')
    op.drop_index('idx_prompt_bundle_phase', table_name='prompt_items')
    op.drop_table('prompt_items')
    op.drop_index('idx_bundle_plan', table_name='prompt_bundles')
    op.drop_index('idx_bundle_project', table_name='prompt_bundles')
    op.drop_table('prompt_bundles')
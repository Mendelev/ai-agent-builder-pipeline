# backend/migrations/versions/004_create_orchestration_tables.py
"""Create orchestration tables

Revision ID: 004
Revises: 003
Create Date: 2024-01-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create enums
    op.execute("CREATE TYPE projectstate AS ENUM ('DRAFT', 'REQS_REFINING', 'REQS_READY', 'CODE_VALIDATED', 'PLAN_READY', 'PROMPTS_READY', 'DONE', 'BLOCKED')")
    op.execute("CREATE TYPE agenttype AS ENUM ('REQUIREMENTS', 'REFINE', 'PLAN', 'PROMPTS', 'VALIDATION')")
    op.execute("CREATE TYPE eventtype AS ENUM ('STATE_TRANSITION', 'AGENT_STARTED', 'AGENT_COMPLETED', 'AGENT_FAILED', 'RETRY_ATTEMPTED', 'USER_ACTION', 'SYSTEM_EVENT')")
    
    # Create state_history table
    op.create_table('state_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_state', postgresql.ENUM('DRAFT', 'REQS_REFINING', 'REQS_READY', 'CODE_VALIDATED', 'PLAN_READY', 'PROMPTS_READY', 'DONE', 'BLOCKED', name='projectstate', create_type=False), nullable=True),
        sa.Column('to_state', postgresql.ENUM('DRAFT', 'REQS_REFINING', 'REQS_READY', 'CODE_VALIDATED', 'PLAN_READY', 'PROMPTS_READY', 'DONE', 'BLOCKED', name='projectstate', create_type=False), nullable=False),
        sa.Column('transition_reason', sa.Text(), nullable=True),
        sa.Column('triggered_by', sa.String(length=100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_state_history_project', 'state_history', ['project_id', 'created_at'])
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('correlation_id', sa.String(length=100), nullable=True),
        sa.Column('event_type', postgresql.ENUM('STATE_TRANSITION', 'AGENT_STARTED', 'AGENT_COMPLETED', 'AGENT_FAILED', 'RETRY_ATTEMPTED', 'USER_ACTION', 'SYSTEM_EVENT', name='eventtype', create_type=False), nullable=False),
        sa.Column('agent_type', postgresql.ENUM('REQUIREMENTS', 'REFINE', 'PLAN', 'PROMPTS', 'VALIDATION', name='agenttype', create_type=False), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('duration_ms', sa.Float(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_project', 'audit_logs', ['project_id', 'created_at'])
    op.create_index('idx_audit_correlation', 'audit_logs', ['correlation_id'])
    op.create_index('idx_audit_event_type', 'audit_logs', ['event_type', 'created_at'])
    
    # Create domain_events table
    op.create_table('domain_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aggregate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aggregate_type', sa.String(length=50), nullable=False),
        sa.Column('event_name', sa.String(length=100), nullable=False),
        sa.Column('event_version', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_domain_event_aggregate', 'domain_events', ['aggregate_id', 'created_at'])
    op.create_index('idx_domain_event_name', 'domain_events', ['event_name', 'created_at'])
    op.create_index('idx_domain_event_unprocessed', 'domain_events', ['processed_at', 'created_at'])
    
    # Create dedup_keys table
    op.create_table('dedup_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_type', postgresql.ENUM('REQUIREMENTS', 'REFINE', 'PLAN', 'PROMPTS', 'VALIDATION', name='agenttype', create_type=False), nullable=False),
        sa.Column('input_hash', sa.String(length=64), nullable=False),
        sa.Column('task_id', sa.String(length=100), nullable=True),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_dedup_key', 'dedup_keys', ['project_id', 'agent_type', 'input_hash'], unique=True)
    op.create_index('idx_dedup_expires', 'dedup_keys', ['expires_at'])

def downgrade() -> None:
    op.drop_index('idx_dedup_expires', table_name='dedup_keys')
    op.drop_index('idx_dedup_key', table_name='dedup_keys')
    op.drop_table('dedup_keys')
    op.drop_index('idx_domain_event_unprocessed', table_name='domain_events')
    op.drop_index('idx_domain_event_name', table_name='domain_events')
    op.drop_index('idx_domain_event_aggregate', table_name='domain_events')
    op.drop_table('domain_events')
    op.drop_index('idx_audit_event_type', table_name='audit_logs')
    op.drop_index('idx_audit_correlation', table_name='audit_logs')
    op.drop_index('idx_audit_project', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('idx_state_history_project', table_name='state_history')
    op.drop_table('state_history')
    op.execute('DROP TYPE eventtype')
    op.execute('DROP TYPE agenttype')
    op.execute('DROP TYPE projectstate')
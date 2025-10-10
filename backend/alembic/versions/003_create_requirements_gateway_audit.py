"""create requirements_gateway_audit table

Revision ID: 003
Revises: 002
Create Date: 2025-10-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from app.core.types import UUID as CustomUUID

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create requirements_gateway_audit table
    op.create_table(
        'requirements_gateway_audit',
        sa.Column('id', CustomUUID(), primary_key=True),
        sa.Column('project_id', CustomUUID(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('correlation_id', CustomUUID(), nullable=False),
        sa.Column('request_id', CustomUUID(), nullable=False, unique=True),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('from_state', sa.String(50), nullable=False),
        sa.Column('to_state', sa.String(50), nullable=False),
        sa.Column('user_id', CustomUUID(), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for performance optimization
    op.create_index('ix_requirements_gateway_audit_project_id', 'requirements_gateway_audit', ['project_id'])
    op.create_index('ix_requirements_gateway_audit_correlation_id', 'requirements_gateway_audit', ['correlation_id'])
    op.create_index('ix_requirements_gateway_audit_request_id', 'requirements_gateway_audit', ['request_id'])
    op.create_index('ix_requirements_gateway_audit_action', 'requirements_gateway_audit', ['action'])
    op.create_index('ix_requirements_gateway_audit_created_at', 'requirements_gateway_audit', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_requirements_gateway_audit_created_at', 'requirements_gateway_audit')
    op.drop_index('ix_requirements_gateway_audit_action', 'requirements_gateway_audit')
    op.drop_index('ix_requirements_gateway_audit_request_id', 'requirements_gateway_audit')
    op.drop_index('ix_requirements_gateway_audit_correlation_id', 'requirements_gateway_audit')
    op.drop_index('ix_requirements_gateway_audit_project_id', 'requirements_gateway_audit')
    
    # Drop table
    op.drop_table('requirements_gateway_audit')
"""create code_repos table

Revision ID: 004
Revises: 003
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from app.core.types import UUID as CustomUUID

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create code_repos table
    op.create_table(
        'code_repos',
        sa.Column('id', CustomUUID(), primary_key=True),
        sa.Column('project_id', CustomUUID(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('git_url', sa.Text(), nullable=False),
        sa.Column('token_ciphertext', sa.LargeBinary(), nullable=False),
        sa.Column('token_kid', sa.Text(), nullable=False),
        sa.Column('repository_size_mb', sa.Numeric(10, 2), nullable=True),
        sa.Column('clone_status', sa.Text(), nullable=False, server_default='PENDING'),
        sa.Column('sandbox_path', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for performance optimization
    op.create_index('ix_code_repos_project_id', 'code_repos', ['project_id'])
    op.create_index('ix_code_repos_clone_status', 'code_repos', ['clone_status'])
    op.create_index('ix_code_repos_created_at', 'code_repos', ['created_at'])
    op.create_index('ix_code_repos_token_kid', 'code_repos', ['token_kid'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_code_repos_token_kid', 'code_repos')
    op.drop_index('ix_code_repos_created_at', 'code_repos')
    op.drop_index('ix_code_repos_clone_status', 'code_repos')
    op.drop_index('ix_code_repos_project_id', 'code_repos')
    
    # Drop table
    op.drop_table('code_repos')

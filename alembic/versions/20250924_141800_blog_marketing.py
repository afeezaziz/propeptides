"""Blog marketing: newsletter_subscriber table and post.view_count

Revision ID: 20250924_141800
Revises: 20250924_132700
Create Date: 2025-09-24 14:18:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250924_141800'
down_revision = '20250924_132700'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add view_count to post
    with op.batch_alter_table('post') as batch_op:
        batch_op.add_column(sa.Column('view_count', sa.Integer(), nullable=True, server_default='0'))

    # Create newsletter_subscriber table
    op.create_table(
        'newsletter_subscriber',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('name', sa.String(length=120), nullable=True),
        sa.Column('utm_source', sa.String(length=100), nullable=True),
        sa.Column('utm_medium', sa.String(length=100), nullable=True),
        sa.Column('utm_campaign', sa.String(length=100), nullable=True),
        sa.Column('referrer', sa.String(length=500), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('unsubscribe_token', sa.String(length=64), nullable=True, unique=True),
        sa.Column('unsubscribed_at', sa.DateTime(), nullable=True),
        sa.Column('confirmed', sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.create_index('ix_newsletter_subscriber_email', 'newsletter_subscriber', ['email'], unique=True)
    op.create_index('ix_newsletter_subscriber_unsubscribe_token', 'newsletter_subscriber', ['unsubscribe_token'], unique=True)
    op.create_index('ix_newsletter_subscriber_created_at', 'newsletter_subscriber', ['created_at'])


def downgrade() -> None:
    # Drop newsletter_subscriber
    op.drop_index('ix_newsletter_subscriber_unsubscribe_token', table_name='newsletter_subscriber')
    op.drop_index('ix_newsletter_subscriber_created_at', table_name='newsletter_subscriber')
    op.drop_index('ix_newsletter_subscriber_email', table_name='newsletter_subscriber')
    op.drop_table('newsletter_subscriber')

    # Remove view_count
    with op.batch_alter_table('post') as batch_op:
        batch_op.drop_column('view_count')

"""Favorites (Wishlist) and Stock Alerts tables

Revision ID: 20250924_132700
Revises: 20250924_110500
Create Date: 2025-09-24 13:27:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250924_132700'
down_revision = '20250924_110500'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # favorite_product
    op.create_table(
        'favorite_product',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('product.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_favorite_product'),
    )
    op.create_index('ix_favorite_product_user_id', 'favorite_product', ['user_id'])
    op.create_index('ix_favorite_product_product_id', 'favorite_product', ['product_id'])

    # stock_alert
    op.create_table(
        'stock_alert',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('product.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
        sa.Column('notified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_stock_alert_product_id', 'stock_alert', ['product_id'])
    op.create_index('ix_stock_alert_user_email', 'stock_alert', ['user_id', 'email'])


def downgrade() -> None:
    op.drop_index('ix_stock_alert_user_email', table_name='stock_alert')
    op.drop_index('ix_stock_alert_product_id', table_name='stock_alert')
    op.drop_table('stock_alert')

    op.drop_index('ix_favorite_product_product_id', table_name='favorite_product')
    op.drop_index('ix_favorite_product_user_id', table_name='favorite_product')
    op.drop_table('favorite_product')

"""Add PDP quality fields to product

Revision ID: 20250925_130300
Revises: 20250924_141800
Create Date: 2025-09-25 13:03:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250925_130300'
down_revision = '20250924_141800'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('product') as batch_op:
        batch_op.add_column(sa.Column('coa_url', sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column('hplc_image', sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column('ms_image', sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column('last_tested_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('lot_number', sa.String(length=100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('product') as batch_op:
        batch_op.drop_column('lot_number')
        batch_op.drop_column('last_tested_at')
        batch_op.drop_column('ms_image')
        batch_op.drop_column('hplc_image')
        batch_op.drop_column('coa_url')

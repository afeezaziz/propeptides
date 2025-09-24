"""Community + SearchDocument (pgvector) tables

Revision ID: 20250924_110500
Revises: 
Create Date: 2025-09-24 11:05:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '20250924_110500'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name in ('postgresql', 'postgres')

    # Enable pgvector extension when using Postgres
    if is_pg:
        op.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))

    # community_post
    op.create_table(
        'community_post',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=200), nullable=False, unique=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='published'),
        sa.Column('view_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('comment_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('score', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # community_comment
    op.create_table(
        'community_comment',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('community_post.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    # community_vote
    op.create_table(
        'community_vote',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('community_post.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('post_id', 'user_id', name='uq_community_vote'),
    )

    # community_tag
    op.create_table(
        'community_tag',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True),
        sa.Column('slug', sa.String(length=100), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    # association table
    op.create_table(
        'community_post_tags',
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('community_post.id'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('community_tag.id'), primary_key=True),
    )

    # search_document with pgvector embedding when available
    try:
        from pgvector.sqlalchemy import Vector as PGVector  # type: ignore
    except Exception:
        PGVector = None

    emb_type = sa.LargeBinary()
    if is_pg and PGVector is not None:
        emb_type = PGVector(1536)  # type: ignore

    op.create_table(
        'search_document',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('ref_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('embedding', emb_type, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('kind', 'ref_id', name='uq_search_document_kind_ref'),
    )

    # Optional: ivfflat index for cosine distance (Postgres + pgvector)
    if is_pg:
        try:
            bind.execute(text('CREATE INDEX IF NOT EXISTS idx_search_document_embedding ON search_document USING ivfflat (embedding vector_cosine_ops)'))
        except Exception:
            # If ivfflat isn't available, ignore
            pass


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name in ('postgresql', 'postgres')

    # Drop tables in reverse order
    op.drop_table('search_document')
    op.drop_table('community_post_tags')
    op.drop_table('community_tag')
    op.drop_table('community_vote')
    op.drop_table('community_comment')
    op.drop_table('community_post')

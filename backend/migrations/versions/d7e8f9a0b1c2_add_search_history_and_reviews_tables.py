"""Add search_history and reviews tables

Revision ID: d7e8f9a0b1c2
Revises: a91a3f924547
Create Date: 2026-08-24 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7e8f9a0b1c2'
down_revision = 'a91a3f924547'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'search_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('query', sa.String(length=255), nullable=False),
        sa.Column('results_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_history_created_at'), 'search_history', ['created_at'], unique=False)
    op.create_index(op.f('ix_search_history_user_id'), 'search_history', ['user_id'], unique=False)

    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='chk_review_rating_range'),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='chk_review_status_valid'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_user_product_review')
    )
    op.create_index(op.f('ix_reviews_product_id'), 'reviews', ['product_id'], unique=False)
    op.create_index(op.f('ix_reviews_status'), 'reviews', ['status'], unique=False)
    op.create_index(op.f('ix_reviews_user_id'), 'reviews', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_reviews_user_id'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_status'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_product_id'), table_name='reviews')
    op.drop_table('reviews')
    op.drop_index(op.f('ix_search_history_user_id'), table_name='search_history')
    op.drop_index(op.f('ix_search_history_created_at'), table_name='search_history')
    op.drop_table('search_history')

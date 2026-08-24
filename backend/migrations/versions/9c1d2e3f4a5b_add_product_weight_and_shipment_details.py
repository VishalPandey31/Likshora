"""Add product weight and shipment extended detail columns

Revision ID: 9c1d2e3f4a5b
Revises: 7a8b9c0d1e2f
Create Date: 2026-08-23 19:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c1d2e3f4a5b'
down_revision = '7a8b9c0d1e2f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('weight', sa.Numeric(precision=10, scale=3), server_default='0.500', nullable=False))

    with op.batch_alter_table('shipments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pickup_token_number', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('label_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('manifest_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('error_message', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('shipments', schema=None) as batch_op:
        batch_op.drop_column('error_message')
        batch_op.drop_column('manifest_url')
        batch_op.drop_column('label_url')
        batch_op.drop_column('pickup_token_number')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('weight')

"""Merge migration heads

Revision ID: 365e06485900
Revises: 9c1d2e3f4a5b, d7e8f9a0b1c2
Create Date: 2026-08-24 14:22:02.460702

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '365e06485900'
down_revision = ('9c1d2e3f4a5b', 'd7e8f9a0b1c2')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

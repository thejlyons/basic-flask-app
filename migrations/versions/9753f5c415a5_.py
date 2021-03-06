"""empty message

Revision ID: 9753f5c415a5
Revises: f42939cfcf5d
Create Date: 2021-01-24 15:05:19.493543

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9753f5c415a5'
down_revision = 'f42939cfcf5d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('redeemed_offers', sa.JSON(), server_default='[]', nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'redeemed_offers')
    # ### end Alembic commands ###

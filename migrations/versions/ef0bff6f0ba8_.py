"""empty message

Revision ID: ef0bff6f0ba8
Revises: 6cc0ac9042a6
Create Date: 2021-02-03 11:13:00.340485

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef0bff6f0ba8'
down_revision = '6cc0ac9042a6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('merchant', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('merchant', sa.Column('longitude', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('merchant', 'longitude')
    op.drop_column('merchant', 'latitude')
    # ### end Alembic commands ###

"""empty message

Revision ID: f70519ef507b
Revises: 82d11ad21244
Create Date: 2021-02-24 14:52:24.381097

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f70519ef507b'
down_revision = '82d11ad21244'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('merchant_contact', sa.Column('locations', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('merchant_contact', 'locations')
    # ### end Alembic commands ###

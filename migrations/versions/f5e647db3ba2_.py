"""empty message

Revision ID: f5e647db3ba2
Revises: 9753f5c415a5
Create Date: 2021-01-24 15:28:26.947531

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5e647db3ba2'
down_revision = '9753f5c415a5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('offer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('merchant_id', sa.Integer(), nullable=True),
    sa.Column('hours', sa.JSON(), server_default='[]', nullable=True),
    sa.Column('offer', sa.String(), nullable=True),
    sa.Column('details', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('code_link', sa.String(), nullable=True),
    sa.Column('deal_limit', sa.Integer(), nullable=True),
    sa.Column('value', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['merchant_id'], ['merchant.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('offer')
    # ### end Alembic commands ###
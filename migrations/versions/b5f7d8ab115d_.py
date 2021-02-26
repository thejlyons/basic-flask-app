"""empty message

Revision ID: b5f7d8ab115d
Revises: bbd24628a3cb
Create Date: 2021-02-04 09:23:21.697537

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5f7d8ab115d'
down_revision = 'bbd24628a3cb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('merchant', sa.Column('approved', sa.Boolean(), server_default='f', nullable=False))
    op.add_column('merchant', sa.Column('coming_soon', sa.Boolean(), server_default='f', nullable=False))
    op.add_column('user', sa.Column('fundraiser_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user', 'fundraiser', ['fundraiser_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_column('user', 'fundraiser_id')
    op.drop_column('merchant', 'coming_soon')
    op.drop_column('merchant', 'approved')
    # ### end Alembic commands ###

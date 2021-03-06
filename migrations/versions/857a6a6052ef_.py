"""empty message

Revision ID: 857a6a6052ef
Revises: 2b5adc8436a9
Create Date: 2021-01-25 11:39:15.546457

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '857a6a6052ef'
down_revision = '2b5adc8436a9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('promo_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user', 'promo_code', ['promo_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_column('user', 'promo_id')
    # ### end Alembic commands ###

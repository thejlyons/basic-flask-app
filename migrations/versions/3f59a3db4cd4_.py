"""empty message

Revision ID: 3f59a3db4cd4
Revises: 5320413b1077
Create Date: 2021-02-24 08:10:42.539251

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f59a3db4cd4'
down_revision = '5320413b1077'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('redemption', sa.Column('offer_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'redemption', 'offer', ['offer_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'redemption', type_='foreignkey')
    op.drop_column('redemption', 'offer_id')
    # ### end Alembic commands ###

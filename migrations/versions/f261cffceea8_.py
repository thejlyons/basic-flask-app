"""empty message

Revision ID: f261cffceea8
Revises: b5f7d8ab115d
Create Date: 2021-02-10 10:05:59.316363

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f261cffceea8'
down_revision = 'b5f7d8ab115d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('region', sa.Column('carousel', sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('region', 'carousel')
    # ### end Alembic commands ###
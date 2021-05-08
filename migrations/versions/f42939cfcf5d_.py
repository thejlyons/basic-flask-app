"""empty message

Revision ID: f42939cfcf5d
Revises: 96ff5bd73c47
Create Date: 2021-01-22 14:14:30.883052

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f42939cfcf5d'
down_revision = '96ff5bd73c47'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('merchant', sa.Column('created', sa.DateTime(), nullable=True))
    op.drop_column('merchant', 'created_s')
    op.add_column('redemption', sa.Column('created', sa.DateTime(), nullable=True))
    op.drop_column('redemption', 'created_s')
    op.add_column('sms_log', sa.Column('created', sa.DateTime(), nullable=True))
    op.drop_column('sms_log', 'created_s')
    op.add_column('user', sa.Column('created', sa.DateTime(), nullable=True))
    op.drop_column('user', 'created_s')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('created_s', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.drop_column('user', 'created')
    op.add_column('sms_log', sa.Column('created_s', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.drop_column('sms_log', 'created')
    op.add_column('redemption', sa.Column('created_s', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.drop_column('redemption', 'created')
    op.add_column('merchant', sa.Column('created_s', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.drop_column('merchant', 'created')
    # ### end Alembic commands ###
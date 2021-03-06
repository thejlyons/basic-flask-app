"""empty message

Revision ID: 2fd95bbaac7b
Revises: 239252e5b613
Create Date: 2021-01-22 06:31:31.625765

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2fd95bbaac7b'
down_revision = '239252e5b613'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('expo_push_tokens', sa.JSON(), server_default='[]', nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'expo_push_tokens')
    # ### end Alembic commands ###

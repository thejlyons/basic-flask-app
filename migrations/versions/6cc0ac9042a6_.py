"""empty message

Revision ID: 6cc0ac9042a6
Revises: 45f136dcbb9f
Create Date: 2021-02-03 11:04:27.707595

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6cc0ac9042a6'
down_revision = '45f136dcbb9f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('daily_activity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('user', sa.Column('city', sa.String(), nullable=True))
    op.add_column('user', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('user', sa.Column('longitude', sa.Float(), nullable=True))
    op.add_column('user', sa.Column('state', sa.String(), nullable=True))
    op.add_column('user', sa.Column('zip_code', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'zip_code')
    op.drop_column('user', 'state')
    op.drop_column('user', 'longitude')
    op.drop_column('user', 'latitude')
    op.drop_column('user', 'city')
    op.drop_table('daily_activity')
    # ### end Alembic commands ###
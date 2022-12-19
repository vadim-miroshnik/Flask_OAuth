"""email_for_user

Revision ID: 8d8503693622
Revises: c086140a4bc1
Create Date: 2022-12-19 09:50:43.006281

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8d8503693622'
down_revision = 'c086140a4bc1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_sign_in_other')
    op.drop_table('user_sign_in_mobile')
    op.drop_table('user_sign_in_web')
    with op.batch_alter_table('history', schema=None) as batch_op:
        batch_op.create_unique_constraint(None, ['id', 'user_device_type'])

    with op.batch_alter_table('roles', schema=None) as batch_op:
        batch_op.create_unique_constraint(None, ['id'])

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(), nullable=True))
        batch_op.create_unique_constraint(None, ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('email')

    with op.batch_alter_table('roles', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')

    with op.batch_alter_table('history', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')

    op.create_table('user_sign_in_web',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('user_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('dt', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('login', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('ip', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('user_agent', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('user_device_type', sa.TEXT(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='history_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', 'user_device_type', name='user_sign_in_web_pkey')
    )
    op.create_table('user_sign_in_mobile',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('user_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('dt', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('login', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('ip', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('user_agent', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('user_device_type', sa.TEXT(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='history_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', 'user_device_type', name='user_sign_in_mobile_pkey')
    )
    op.create_table('user_sign_in_other',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('user_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('dt', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('login', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('ip', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('user_agent', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('user_device_type', sa.TEXT(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='history_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', 'user_device_type', name='user_sign_in_other_pkey')
    )
    # ### end Alembic commands ###

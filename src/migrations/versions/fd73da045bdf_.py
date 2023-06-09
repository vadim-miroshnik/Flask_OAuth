"""empty message

Revision ID: fd73da045bdf
Revises: 
Create Date: 2022-12-13 23:33:46.413409

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from core.db import db

# revision identifiers, used by Alembic.
revision = 'fd73da045bdf'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('roles',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('token',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('time_created', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('expired_time', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('login', sa.String(), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('login')
    )
    op.create_table('association_user_roles',
    sa.Column('users_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('roles_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['roles_id'], ['roles.id'], ),
    sa.ForeignKeyConstraint(['users_id'], ['users.id'], )
    )
    op.create_table('history',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('dt', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('login', sa.String(), nullable=False),
    sa.Column('ip', sa.String(), nullable=False),
    sa.Column('user_agent', sa.String(), nullable=False),
    sa.Column('user_device_type', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id', 'user_device_type'),
    sa.UniqueConstraint('id', 'user_device_type'),
    postgresql_partition_by='LIST (user_device_type)'
    )
    op.execute("""CREATE TABLE IF NOT EXISTS "user_sign_in_other" PARTITION OF "history" FOR VALUES IN ('other')""")
    op.execute("""CREATE TABLE IF NOT EXISTS "user_sign_in_mobile" PARTITION OF "history" FOR VALUES IN ('mobile')""")
    op.execute("""CREATE TABLE IF NOT EXISTS "user_sign_in_web" PARTITION OF "history" FOR VALUES IN ('web')""")
    op.create_table('permissions',
    sa.Column('name', sa.Enum('all_read', 'all_write', name='permissiontype'), nullable=False),
    sa.Column('id_role', postgresql.UUID(as_uuid=True), nullable=True),
    sa.ForeignKeyConstraint(['id_role'], ['roles.id'], ),
    sa.PrimaryKeyConstraint('name')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('permissions')
    op.drop_table('history')
    op.drop_table('association_user_roles')
    op.drop_table('users')
    op.drop_table('token')
    op.drop_table('roles')
    # ### end Alembic commands ###

"""Initial migration

Revision ID: 53a078d140ee
Revises: 
Create Date: 2025-02-17 00:35:45.091119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import fastapi_users_db_sqlalchemy.generics
import app.models.groups


# revision identifiers, used by Alembic.
revision: str = '53a078d140ee'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('group',
    sa.Column('group_name', sa.String(length=200), nullable=False),
    sa.Column('group_desc', sa.String(length=1024), nullable=True),
    sa.Column('permission', app.models.groups.Permission(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('group_name')
    )
    op.create_table('roles',
    sa.Column('role_name', sa.String(length=200), nullable=False),
    sa.Column('role_desc', sa.String(length=1024), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('role_name')
    )
    op.create_table('user_profiles',
    sa.Column('first_name', sa.String(length=120), nullable=False),
    sa.Column('last_name', sa.String(length=120), nullable=False),
    sa.Column('gender', sa.String(length=10), nullable=True),
    sa.Column('date_of_birth', sa.DateTime(timezone=True), nullable=True),
    sa.Column('city', sa.String(length=50), nullable=True),
    sa.Column('country', sa.String(length=50), nullable=True),
    sa.Column('address', sa.String(length=255), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('company', sa.String(length=100), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_profiles_first_name'), 'user_profiles', ['first_name'], unique=False)
    op.create_index(op.f('ix_user_profiles_last_name'), 'user_profiles', ['last_name'], unique=False)
    op.create_table('users',
    sa.Column('created', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('role_id', sa.Uuid(), nullable=True),
    sa.Column('profile_id', sa.Uuid(), nullable=True),
    sa.Column('id', fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('hashed_password', sa.String(length=1024), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['profile_id'], ['user_profiles.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('group_users',
    sa.Column('group_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['group.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('upload',
    sa.Column('name', sa.String(length=250), nullable=False),
    sa.Column('unique_name', sa.String(length=50), nullable=False),
    sa.Column('file_type', sa.String(), nullable=False),
    sa.Column('source', sa.String(), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=True),
    sa.Column('user_id', fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('unique_name')
    )
    op.create_table('user_activity',
    sa.Column('user_id', fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
    sa.Column('activity_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('activity_type', sa.String(length=200), nullable=False),
    sa.Column('activity_desc', sa.String(length=1024), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_activity')
    op.drop_table('upload')
    op.drop_table('group_users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_user_profiles_last_name'), table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_first_name'), table_name='user_profiles')
    op.drop_table('user_profiles')
    op.drop_table('roles')
    op.drop_table('group')
    # ### end Alembic commands ###

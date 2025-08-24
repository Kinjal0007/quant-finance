"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import context

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get the database dialect
    dialect = context.get_bind().dialect.name
    
    # Create users table
    if dialect == 'postgresql':
        # PostgreSQL-specific columns
        op.create_table('users',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    else:
        # SQLite-compatible columns
        op.create_table('users',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create jobs table
    if dialect == 'postgresql':
        # PostgreSQL-specific columns
        op.create_table('jobs',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('type', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('params_json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
            sa.Column('symbols', postgresql.JSON(astext_type=sa.Text()), nullable=False),
            sa.Column('start_ts', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_ts', sa.DateTime(timezone=True), nullable=False),
            sa.Column('interval', sa.String(length=20), nullable=False),
            sa.Column('vendor', sa.String(length=20), nullable=False),
            sa.Column('adjusted', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('result_refs', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('error', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    else:
        # SQLite-compatible columns
        op.create_table('jobs',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('type', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('params_json', sa.Text(), nullable=False),
            sa.Column('symbols', sa.Text(), nullable=False),
            sa.Column('start_ts', sa.DateTime(), nullable=False),
            sa.Column('end_ts', sa.DateTime(), nullable=False),
            sa.Column('interval', sa.String(length=20), nullable=False),
            sa.Column('vendor', sa.String(length=20), nullable=False),
            sa.Column('adjusted', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('finished_at', sa.DateTime(), nullable=True),
            sa.Column('result_refs', sa.Text(), nullable=True),
            sa.Column('error', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create indexes
    op.create_index(op.f('ix_jobs_type'), 'jobs', ['type'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)
    op.create_index('idx_jobs_user_created', 'jobs', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_jobs_status_created', 'jobs', ['status', 'created_at'], unique=False)
    op.create_index('idx_jobs_type_status', 'jobs', ['type', 'status'], unique=False)
    
    # Add foreign key constraint only for PostgreSQL
    if dialect == 'postgresql':
        op.create_foreign_key(None, 'jobs', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    # Get the database dialect
    dialect = context.get_bind().dialect.name
    
    # Remove foreign key constraint only for PostgreSQL
    if dialect == 'postgresql':
        op.drop_constraint(None, 'jobs', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('idx_jobs_type_status', table_name='jobs')
    op.drop_index('idx_jobs_status_created', table_name='jobs')
    op.drop_index('idx_jobs_user_created', table_name='jobs')
    op.drop_index(op.f('ix_jobs_status'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_type'), table_name='jobs')
    
    # Drop tables
    op.drop_table('jobs')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

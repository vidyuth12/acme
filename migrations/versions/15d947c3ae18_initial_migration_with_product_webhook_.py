"""Initial migration with Product, Webhook, and ImportJob models

Revision ID: 15d947c3ae18
Revises: 
Create Date: 2025-11-18 23:38:59.788764

"""
from alembic import op
import sqlalchemy as sa


revision = '15d947c3ae18'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('import_jobs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('filename', sa.String(length=500), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('total_rows', sa.Integer(), nullable=True),
    sa.Column('processed_rows', sa.Integer(), nullable=True),
    sa.Column('success_count', sa.Integer(), nullable=True),
    sa.Column('error_count', sa.Integer(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sku', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.execute('CREATE UNIQUE INDEX ix_products_sku_lower ON products (LOWER(sku))')
    
    op.create_table('webhooks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(length=1000), nullable=False),
    sa.Column('event_type', sa.String(length=100), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('webhooks')
    op.execute('DROP INDEX IF EXISTS ix_products_sku_lower')
    op.drop_table('products')
    op.drop_table('import_jobs')

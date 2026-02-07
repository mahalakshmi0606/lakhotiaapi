"""Add stock_id, quantity, auto_calculate_count with unique fix

Revision ID: 37d9189e449f
Revises: 32193e657356
Create Date: 2026-01-12 18:05:35.673604
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '37d9189e449f'
down_revision = '32193e657356'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns first
    with op.batch_alter_table('stocks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stock_id', sa.String(length=100), nullable=True))  # temporarily nullable
        batch_op.add_column(sa.Column('quantity', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('auto_calculate_count', sa.Float(), nullable=True))
        batch_op.alter_column('length',
               existing_type=mysql.VARCHAR(length=50),
               type_=sa.Float(),
               existing_nullable=True)
        batch_op.alter_column('width',
               existing_type=mysql.VARCHAR(length=50),
               type_=sa.Float(),
               existing_nullable=True)

    # Populate unique stock_id for existing rows
    op.execute("""
        SET @i = 0;
        UPDATE stocks
        SET stock_id = CONCAT('STOCK_', (@i := @i + 1))
        WHERE stock_id IS NULL OR stock_id = '';
    """)

    # Now alter stock_id to be non-nullable and unique
    with op.batch_alter_table('stocks', schema=None) as batch_op:
        batch_op.alter_column('stock_id',
               existing_type=sa.String(length=100),
               nullable=False)
        batch_op.create_unique_constraint(None, ['stock_id'])


def downgrade():
    # Drop unique constraint first
    with op.batch_alter_table('stocks', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('auto_calculate_count')
        batch_op.drop_column('quantity')
        batch_op.drop_column('stock_id')

    # Revert length and width columns
    with op.batch_alter_table('stocks', schema=None) as batch_op:
        batch_op.alter_column('width',
               existing_type=sa.Float(),
               type_=mysql.VARCHAR(length=50),
               existing_nullable=True)
        batch_op.alter_column('length',
               existing_type=sa.Float(),
               type_=mysql.VARCHAR(length=50),
               existing_nullable=True)

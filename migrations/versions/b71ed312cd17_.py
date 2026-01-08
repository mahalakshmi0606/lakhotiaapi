"""empty message

Revision ID: b71ed312cd17
Revises: 27888a3c0b14
Create Date: 2026-01-04 23:31:53.865929
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'b71ed312cd17'
down_revision = '27888a3c0b14'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('grn', schema=None) as batch_op:
        # ❌ REMOVED po_number (already exists in DB)

        batch_op.add_column(sa.Column('company_name', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('company_address', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('customer_mobile', sa.String(length=15), nullable=True))
        batch_op.add_column(sa.Column('customer_email', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('department', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('gst_number', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('supplier_part_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('supplier_description', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('brand_code', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('brand_description', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('unit', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('quantity', sa.Float(), nullable=False))

        batch_op.alter_column(
            'invoice_number',
            existing_type=mysql.VARCHAR(length=100),
            nullable=False
        )

        batch_op.alter_column(
            'invoice_date',
            existing_type=mysql.VARCHAR(length=20),
            nullable=False
        )

        batch_op.alter_column(
            'customer_name',
            existing_type=mysql.VARCHAR(length=200),
            type_=sa.String(length=100),
            existing_nullable=True
        )

        batch_op.alter_column(
            'item_name',
            existing_type=mysql.VARCHAR(length=200),
            nullable=False
        )

        batch_op.alter_column(
            'buy_price',
            existing_type=mysql.FLOAT(),
            nullable=False
        )

        batch_op.alter_column(
            'batch_code',
            existing_type=mysql.VARCHAR(length=100),
            nullable=False
        )

        batch_op.drop_column('customer_description')
        batch_op.drop_column('customer_part_no')


def downgrade():
    with op.batch_alter_table('grn', schema=None) as batch_op:
        batch_op.add_column(sa.Column('customer_part_no', mysql.VARCHAR(length=100), nullable=True))
        batch_op.add_column(sa.Column('customer_description', mysql.VARCHAR(length=500), nullable=True))

        batch_op.alter_column(
            'batch_code',
            existing_type=mysql.VARCHAR(length=100),
            nullable=True
        )

        batch_op.alter_column(
            'buy_price',
            existing_type=mysql.FLOAT(),
            nullable=True
        )

        batch_op.alter_column(
            'item_name',
            existing_type=mysql.VARCHAR(length=200),
            nullable=True
        )

        batch_op.alter_column(
            'customer_name',
            existing_type=sa.String(length=100),
            type_=mysql.VARCHAR(length=200),
            existing_nullable=True
        )

        batch_op.alter_column(
            'invoice_date',
            existing_type=mysql.VARCHAR(length=20),
            nullable=True
        )

        batch_op.alter_column(
            'invoice_number',
            existing_type=mysql.VARCHAR(length=100),
            nullable=True
        )

        batch_op.drop_column('quantity')
        batch_op.drop_column('unit')
        batch_op.drop_column('brand_description')
        batch_op.drop_column('brand_code')
        batch_op.drop_column('supplier_description')
        batch_op.drop_column('supplier_part_no')
        batch_op.drop_column('gst_number')
        batch_op.drop_column('department')
        batch_op.drop_column('customer_email')
        batch_op.drop_column('customer_mobile')
        batch_op.drop_column('company_address')
        batch_op.drop_column('company_name')
        # ❌ REMOVED po_number here as well

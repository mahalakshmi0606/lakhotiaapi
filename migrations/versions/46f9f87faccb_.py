"""fix stock_id duplicates before adding unique constraint

Revision ID: 46f9f87faccb
Revises: 37d9189e449f
Create Date: 2026-01-23 12:06:14.964796
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '46f9f87faccb'
down_revision = '37d9189e449f'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1️⃣ Fix empty or NULL stock_id
    conn.execute(text("""
        UPDATE stocks
        SET stock_id = CONCAT('STOCK-', id)
        WHERE stock_id = '' OR stock_id IS NULL
    """))

    # 2️⃣ Fix any remaining duplicates
    conn.execute(text("""
        UPDATE stocks s1
        JOIN stocks s2
          ON s1.stock_id = s2.stock_id
         AND s1.id > s2.id
        SET s1.stock_id = CONCAT(s1.stock_id, '-', s1.id)
    """))

    # 3️⃣ Add UNIQUE constraint safely
    with op.batch_alter_table('stocks') as batch_op:
        batch_op.create_unique_constraint(
            'uq_stocks_stock_id',
            ['stock_id']
        )


def downgrade():
    with op.batch_alter_table('stocks') as batch_op:
        batch_op.drop_constraint(
            'uq_stocks_stock_id',
            type_='unique'
        )

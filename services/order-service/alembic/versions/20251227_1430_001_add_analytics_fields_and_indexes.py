"""Add analytics fields and indexes for Order model and create CustomerItemPreference model

Revision ID: 001
Revises:
Create Date: 2025-12-27 14:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add new fields to Order table for analytics:
    - customer_id (UUID, nullable, indexed)
    - customer_email (String, nullable, indexed)
    - order_type (Enum, non-nullable, default 'TABLE', indexed)
    - delivery_address (Text, nullable)

    Add index to existing customer_phone field

    Create CustomerItemPreference table for tracking customer preferences

    Add comprehensive indexes for analytics queries
    """

    # Step 1: Create OrderType enum type
    order_type_enum = postgresql.ENUM('TABLE', 'ONLINE', name='ordertype', create_type=True)
    order_type_enum.create(op.get_bind(), checkfirst=True)

    # Step 2: Add new columns to orders table (all nullable first for backward compatibility)
    op.add_column('orders', sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('orders', sa.Column('customer_email', sa.String(length=255), nullable=True))
    op.add_column('orders', sa.Column('order_type', sa.Enum('TABLE', 'ONLINE', name='ordertype'), nullable=True))
    op.add_column('orders', sa.Column('delivery_address', sa.Text(), nullable=True))

    # Step 3: Backfill existing orders with default order_type = 'TABLE'
    op.execute("UPDATE orders SET order_type = 'TABLE' WHERE order_type IS NULL")

    # Step 4: Make order_type non-nullable after backfill
    op.alter_column('orders', 'order_type', nullable=False, server_default='TABLE')

    # Step 5: Add indexes to orders table for analytics performance
    op.create_index('idx_orders_customer_id', 'orders', ['customer_id'], unique=False)
    op.create_index('idx_orders_customer_email', 'orders', ['customer_email'], unique=False,
                    postgresql_where=sa.text('customer_email IS NOT NULL'))
    op.create_index('idx_orders_customer_phone', 'orders', ['customer_phone'], unique=False)
    op.create_index('idx_orders_order_type', 'orders', ['order_type'], unique=False)

    # Composite indexes for common analytics queries
    op.create_index('idx_orders_restaurant_created', 'orders', ['restaurant_id', sa.text('created_at DESC')])
    op.create_index('idx_orders_type_status_created', 'orders', ['order_type', 'status', sa.text('created_at DESC')])

    # Step 6: Add indexes to order_items table for demand prediction
    op.create_index('idx_order_items_menu_created', 'order_items', ['menu_item_id', sa.text('created_at DESC')])
    op.create_index('idx_order_items_composite', 'order_items', ['order_id', 'menu_item_id'], unique=False)

    # Step 7: Create customer_item_preferences table
    op.create_table(
        'customer_item_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_identifier', sa.String(length=255), nullable=False, index=True),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('menu_item_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),

        # RFM Metrics
        sa.Column('order_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_spent', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('recency_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('frequency_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('monetary_score', sa.Float(), nullable=False, server_default='0.0'),

        # Timestamps
        sa.Column('first_ordered_at', sa.DateTime(), nullable=True),
        sa.Column('last_ordered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Step 8: Add composite indexes to customer_item_preferences
    op.create_index('idx_customer_restaurant', 'customer_item_preferences',
                    ['customer_identifier', 'restaurant_id'], unique=False)
    op.create_index('idx_customer_menu_item', 'customer_item_preferences',
                    ['customer_identifier', 'menu_item_id'], unique=False)


def downgrade() -> None:
    """
    Reverse all changes made in upgrade()
    """
    # Drop customer_item_preferences table and its indexes
    op.drop_index('idx_customer_menu_item', table_name='customer_item_preferences')
    op.drop_index('idx_customer_restaurant', table_name='customer_item_preferences')
    op.drop_table('customer_item_preferences')

    # Drop order_items indexes
    op.drop_index('idx_order_items_composite', table_name='order_items')
    op.drop_index('idx_order_items_menu_created', table_name='order_items')

    # Drop orders composite indexes
    op.drop_index('idx_orders_type_status_created', table_name='orders')
    op.drop_index('idx_orders_restaurant_created', table_name='orders')

    # Drop orders single column indexes
    op.drop_index('idx_orders_order_type', table_name='orders')
    op.drop_index('idx_orders_customer_phone', table_name='orders')
    op.drop_index('idx_orders_customer_email', table_name='orders')
    op.drop_index('idx_orders_customer_id', table_name='orders')

    # Drop new columns from orders table
    op.drop_column('orders', 'delivery_address')
    op.drop_column('orders', 'order_type')
    op.drop_column('orders', 'customer_email')
    op.drop_column('orders', 'customer_id')

    # Drop OrderType enum
    order_type_enum = postgresql.ENUM('TABLE', 'ONLINE', name='ordertype')
    order_type_enum.drop(op.get_bind(), checkfirst=True)

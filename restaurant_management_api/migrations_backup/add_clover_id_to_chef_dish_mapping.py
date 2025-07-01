"""
Migration: Add clover_id and item_name columns to chef_dish_mapping
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('chef_dish_mapping', sa.Column('clover_id', sa.String(length=32), nullable=True))
    op.add_column('chef_dish_mapping', sa.Column('item_name', sa.String(length=128), nullable=True))
    op.create_index('ix_chef_dish_mapping_clover_id', 'chef_dish_mapping', ['clover_id'])

def downgrade():
    op.drop_index('ix_chef_dish_mapping_clover_id', table_name='chef_dish_mapping')
    op.drop_column('chef_dish_mapping', 'clover_id')
    op.drop_column('chef_dish_mapping', 'item_name') 
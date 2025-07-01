from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'data_source_config',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('tenant_id', sa.String(64), nullable=True),
        sa.Column('data_type', sa.String(32), nullable=False),
        sa.Column('source', sa.String(32), nullable=False),
        sa.Column('updated_by', sa.String(64), nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_data_source_config_tenant_type', 'data_source_config', ['tenant_id', 'data_type'], unique=True)

def downgrade():
    op.drop_index('ix_data_source_config_tenant_type', table_name='data_source_config')
    op.drop_table('data_source_config') 
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')
print("Using DB:", db_path)
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS data_source_config (
        id INTEGER PRIMARY KEY,
        tenant_id VARCHAR(64),
        data_type VARCHAR(32) NOT NULL,
        source VARCHAR(32) NOT NULL,
        updated_by VARCHAR(64) NOT NULL,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
''')
c.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS ix_data_source_config_tenant_type
    ON data_source_config (tenant_id, data_type)
''')
conn.commit()
conn.close()
print("✅ data_source_config table created (or already exists)") 
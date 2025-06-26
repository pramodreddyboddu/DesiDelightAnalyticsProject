#!/usr/bin/env python3
"""
Script to fix the database by creating the data_source_config table
"""
import sys
import os
import sqlite3

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_data_source_config_table():
    """Create the data_source_config table directly in the database"""
    
    # Get the database path
    database_path = os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')
    
    print(f"Connecting to database: {database_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data_source_config'")
        if cursor.fetchone():
            print("✅ data_source_config table already exists!")
            return True
        
        # Create the table
        cursor.execute('''
            CREATE TABLE data_source_config (
                id INTEGER PRIMARY KEY,
                tenant_id VARCHAR(64),
                data_type VARCHAR(32) NOT NULL,
                source VARCHAR(32) NOT NULL,
                updated_by VARCHAR(64) NOT NULL,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create the index
        cursor.execute('''
            CREATE UNIQUE INDEX ix_data_source_config_tenant_type 
            ON data_source_config (tenant_id, data_type)
        ''')
        
        # Commit the changes
        conn.commit()
        
        # Verify the table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data_source_config'")
        if cursor.fetchone():
            print("✅ data_source_config table created successfully!")
            
            # Insert default configuration
            cursor.execute('''
                INSERT OR REPLACE INTO data_source_config (tenant_id, data_type, source, updated_by, updated_at)
                VALUES (NULL, 'sales', 'local', 'system', CURRENT_TIMESTAMP)
            ''')
            
            cursor.execute('''
                INSERT OR REPLACE INTO data_source_config (tenant_id, data_type, source, updated_by, updated_at)
                VALUES (NULL, 'inventory', 'local', 'system', CURRENT_TIMESTAMP)
            ''')
            
            conn.commit()
            print("✅ Default data source configuration inserted!")
            
            return True
        else:
            print("❌ Table was not created!")
            return False
            
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Creating data_source_config table...")
    success = create_data_source_config_table()
    if success:
        print("🎉 Database fix completed successfully!")
    else:
        print("💥 Database fix failed!")
        sys.exit(1) 
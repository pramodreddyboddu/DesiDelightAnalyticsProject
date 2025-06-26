#!/usr/bin/env python3
"""
Standalone script to create the data_source_config table
"""
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import create_app
app = create_app()
from src.models import db
from src.models.data_source_config import DataSourceConfig
import sqlalchemy as sa

def create_data_source_config_table():
    """Create the data_source_config table"""
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            print("✅ data_source_config table created successfully!")
            
            # Verify the table exists
            inspector = sa.inspect(db.engine)
            tables = inspector.get_table_names()
            if 'data_source_config' in tables:
                print("✅ Table verification successful!")
                return True
            else:
                print("❌ Table was not created!")
                return False
                
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            return False

if __name__ == "__main__":
    print("Creating data_source_config table...")
    success = create_data_source_config_table()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1) 
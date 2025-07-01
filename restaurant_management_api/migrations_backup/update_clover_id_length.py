"""
Migration script to update clover_id field length from 50 to 255 characters.
This fixes the StringDataRightTruncation error when generating longer clover_ids.
"""

import os
import sys
from sqlalchemy import text

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models import db
from src.main import create_app

def update_clover_id_length():
    """Update clover_id field length in item and chef tables"""
    app = create_app()
    
    with app.app_context():
        try:
            # Update item table
            db.session.execute(text("""
                ALTER TABLE item 
                ALTER COLUMN clover_id TYPE VARCHAR(255)
            """))
            print("✅ Updated item.clover_id to VARCHAR(255)")
            
            # Update chef table
            db.session.execute(text("""
                ALTER TABLE chef 
                ALTER COLUMN clover_id TYPE VARCHAR(255)
            """))
            print("✅ Updated chef.clover_id to VARCHAR(255)")
            
            db.session.commit()
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    update_clover_id_length() 
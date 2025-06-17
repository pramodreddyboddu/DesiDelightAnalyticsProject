from flask import Flask
from models import db, Item
import sqlite3
import os

def update_schema():
    # Get the correct database path (src/database/app.db)
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'database', 'app.db')
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List of columns to ensure exist
    new_columns = [
        ('alternate_name', 'TEXT'),
        ('description', 'TEXT'),
        ('price_type', 'VARCHAR(50)'),
        ('price_unit', 'VARCHAR(50)'),
        ('cost', 'FLOAT'),
        ('product_code', 'VARCHAR(50)'),
        ('sku', 'VARCHAR(50)'),
        ('quantity', 'INTEGER'),
        ('is_hidden', 'BOOLEAN'),
        ('default_tax_rates', 'BOOLEAN'),
        ('non_revenue_item', 'BOOLEAN'),
        ('printer_labels', 'VARCHAR(100)'),
        ('modifier_groups', 'VARCHAR(100)'),
        ('category', 'VARCHAR(50)'),
        ('tax_rates', 'VARCHAR(100)'),
        ('variant_attribute', 'VARCHAR(100)'),
        ('variant_option', 'VARCHAR(100)'),
        ('is_active', 'BOOLEAN'),
        ('created_at', 'DATETIME'),
        ('updated_at', 'DATETIME')
    ]
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(item)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    # Add missing columns
    for column_name, column_type in new_columns:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE item ADD COLUMN {column_name} {column_type}")
                print(f"Added column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"Error adding column {column_name}: {str(e)}")
    
    conn.commit()
    conn.close()
    print("Schema update completed - All missing columns added if needed.")

if __name__ == '__main__':
    update_schema() 
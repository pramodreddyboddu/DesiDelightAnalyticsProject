#!/usr/bin/env python3
"""
Safe Migration Script: SQLite to PostgreSQL
This script safely migrates data from SQLite to PostgreSQL without breaking the existing app.
"""

import os
import sys
import sqlite3
import psycopg2
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, sqlite_path, postgres_config):
        self.sqlite_path = sqlite_path
        self.postgres_config = postgres_config
        
    def check_sqlite_exists(self):
        """Check if SQLite database exists"""
        if not os.path.exists(self.sqlite_path):
            logger.error(f"SQLite database not found at {self.sqlite_path}")
            return False
        return True
    
    def connect_sqlite(self):
        """Connect to SQLite database"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            return None
    
    def connect_postgres(self):
        """Connect to PostgreSQL database"""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return None
    
    def get_sqlite_tables(self, conn):
        """Get list of tables from SQLite"""
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]
    
    def get_table_schema(self, conn, table_name):
        """Get table schema from SQLite"""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return cursor.fetchall()
    
    def create_postgres_table(self, pg_conn, table_name, columns):
        """Create table in PostgreSQL"""
        cursor = pg_conn.cursor()
        
        # Map SQLite types to PostgreSQL types
        type_mapping = {
            'INTEGER': 'INTEGER',
            'REAL': 'DOUBLE PRECISION',
            'TEXT': 'TEXT',
            'BLOB': 'BYTEA',
            'BOOLEAN': 'BOOLEAN'
        }
        
        column_definitions = []
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            is_nullable = not col[3]
            is_primary_key = col[5]
            
            pg_type = type_mapping.get(col_type, 'TEXT')
            
            if is_primary_key:
                column_definitions.append(f"{col_name} {pg_type} PRIMARY KEY")
            else:
                nullable = "" if is_nullable else " NOT NULL"
                column_definitions.append(f"{col_name} {pg_type}{nullable}")
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(column_definitions)}
        );
        """
        
        try:
            cursor.execute(create_sql)
            pg_conn.commit()
            logger.info(f"Created table: {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            pg_conn.rollback()
            return False
    
    def migrate_table_data(self, sqlite_conn, pg_conn, table_name):
        """Migrate data from SQLite table to PostgreSQL"""
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        try:
            # Get all data from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                logger.info(f"No data to migrate for table: {table_name}")
                return True
            
            # Get column names
            columns = [description[0] for description in sqlite_cursor.description]
            
            # Prepare insert statement
            placeholders = ', '.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Convert rows to tuples
            data = []
            for row in rows:
                row_data = []
                for col in columns:
                    value = row[col]
                    # Handle None values and data type conversions
                    if value is None:
                        row_data.append(None)
                    elif isinstance(value, bool):
                        row_data.append(1 if value else 0)
                    else:
                        row_data.append(value)
                data.append(tuple(row_data))
            
            # Insert data into PostgreSQL
            pg_cursor.executemany(insert_sql, data)
            pg_conn.commit()
            
            logger.info(f"Migrated {len(rows)} rows from table: {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate table {table_name}: {e}")
            pg_conn.rollback()
            return False
    
    def migrate(self):
        """Perform the complete migration"""
        logger.info("Starting database migration from SQLite to PostgreSQL")
        
        # Check if SQLite database exists
        if not self.check_sqlite_exists():
            return False
        
        # Connect to databases
        sqlite_conn = self.connect_sqlite()
        if not sqlite_conn:
            return False
        
        pg_conn = self.connect_postgres()
        if not pg_conn:
            sqlite_conn.close()
            return False
        
        try:
            # Get list of tables
            tables = self.get_sqlite_tables(sqlite_conn)
            logger.info(f"Found {len(tables)} tables to migrate: {tables}")
            
            # Migrate each table
            for table_name in tables:
                logger.info(f"Migrating table: {table_name}")
                
                # Get table schema
                schema = self.get_table_schema(sqlite_conn, table_name)
                
                # Create table in PostgreSQL
                if not self.create_postgres_table(pg_conn, table_name, schema):
                    continue
                
                # Migrate data
                if not self.migrate_table_data(sqlite_conn, pg_conn, table_name):
                    continue
                
                logger.info(f"Successfully migrated table: {table_name}")
            
            logger.info("Database migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
        
        finally:
            sqlite_conn.close()
            pg_conn.close()

def main():
    """Main migration function"""
    # Configuration
    sqlite_path = "src/database/app.db"  # Path to your SQLite database
    
    postgres_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', 5432),
        'database': os.getenv('POSTGRES_DB', 'desidelight'),
        'user': os.getenv('POSTGRES_USER', 'desidelight_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'desidelight_password')
    }
    
    # Create backup of SQLite database
    backup_path = f"{sqlite_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if os.path.exists(sqlite_path):
        import shutil
        shutil.copy2(sqlite_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
    
    # Perform migration
    migrator = DatabaseMigrator(sqlite_path, postgres_config)
    success = migrator.migrate()
    
    if success:
        logger.info("Migration completed successfully!")
        logger.info("You can now update your DATABASE_URL to use PostgreSQL")
        logger.info("Example: DATABASE_URL=postgresql://user:password@localhost:5432/desidelight")
    else:
        logger.error("Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 
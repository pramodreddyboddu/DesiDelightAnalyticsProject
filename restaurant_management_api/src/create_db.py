import os
import sqlite3
from pathlib import Path

def create_directories():
    # Get the current directory
    current_dir = Path(__file__).parent
    
    # Create database directory
    db_dir = current_dir / 'database'
    db_dir.mkdir(exist_ok=True)
    print(f"Database directory created at: {db_dir}")
    
    # Create session directory
    instance_dir = current_dir.parent / 'instance'
    instance_dir.mkdir(exist_ok=True)
    session_dir = instance_dir / 'flask_session'
    session_dir.mkdir(exist_ok=True)
    print(f"Session directory created at: {session_dir}")
    
    # Create empty database file
    db_file = db_dir / 'app.db'
    if not db_file.exists():
        conn = sqlite3.connect(db_file)
        conn.close()
        print(f"Empty database file created at: {db_file}")

if __name__ == '__main__':
    create_directories() 
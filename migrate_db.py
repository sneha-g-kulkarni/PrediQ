"""
Database Migration Script
Updates user_sessions table to use separate download counters
"""

import sqlite3
import os

# Get database path
project_root = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_root, 'data', 'prediq.db')

print(f"Migrating database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if old column exists
    cursor.execute("PRAGMA table_info(user_sessions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"Current columns: {columns}")
    
    if 'free_downloads_used' in columns:
        print("Old schema detected. Migrating...")
        
        # Create new table with correct schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                prev_year_downloads INTEGER DEFAULT 0,
                practice_downloads INTEGER DEFAULT 0,
                last_reset_date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Copy data from old table
        cursor.execute('''
            INSERT INTO user_sessions_new (id, user_id, prev_year_downloads, practice_downloads, last_reset_date)
            SELECT id, user_id, free_downloads_used, 0, last_reset_date
            FROM user_sessions
        ''')
        
        # Drop old table
        cursor.execute('DROP TABLE user_sessions')
        
        # Rename new table
        cursor.execute('ALTER TABLE user_sessions_new RENAME TO user_sessions')
        
        print("✅ Migration completed successfully!")
        
    elif 'prev_year_downloads' in columns:
        print("✅ Database already has correct schema!")
        
    else:
        print("Creating new table...")
        # Create fresh table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                prev_year_downloads INTEGER DEFAULT 0,
                practice_downloads INTEGER DEFAULT 0,
                last_reset_date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("✅ Table created successfully!")
    
    conn.commit()
    print("\n✅ Database migration complete!")
    
except Exception as e:
    print(f"❌ Error during migration: {e}")
    conn.rollback()
    
finally:
    conn.close()

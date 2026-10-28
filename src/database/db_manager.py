"""
Database Manager for PrediQ Application
Handles SQLite database operations and schema management
"""

import sqlite3
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import threading

class DatabaseManager:
    def __init__(self, db_path: str = None):
        """Initialize database manager with path to SQLite database"""
        if db_path is None:
            # Use data directory in project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            data_dir = os.path.join(project_root, 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'prediq.db')
        
        self.db_path = db_path
        self._local = threading.local()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection with proper settings"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=10.0
            )
            self._local.connection.row_factory = sqlite3.Row  # Enable dict-like access
        return self._local.connection
    
    def close_connection(self):
        """Close thread-local database connection"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results"""
        conn = self.get_connection()
        cursor = conn.execute(query, params)
        return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows"""
        conn = self.get_connection()
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.rowcount
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def initialize_database(self):
        """Create all necessary tables and insert default admin"""
        conn = self.get_connection()
        
        # Users table (students)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                phone VARCHAR(15),
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Admin table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Question papers table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS question_papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                year INTEGER NOT NULL,
                board VARCHAR(20) NOT NULL,  -- CBSE, STATE
                course VARCHAR(10),  -- PCMB, PCMC (for 2nd PU)
                subject VARCHAR(50) NOT NULL,
                class_level VARCHAR(10) NOT NULL,  -- 10th, 2nd_PU
                file_path VARCHAR(500) NOT NULL,
                uploaded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_by INTEGER,
                FOREIGN KEY (uploaded_by) REFERENCES admin(id)
            )
        ''')
        
        # Questions extracted from papers
        conn.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                question_type VARCHAR(20),  -- MCQ, SHORT, LONG
                marks INTEGER DEFAULT 1,
                difficulty_level VARCHAR(10) DEFAULT 'MEDIUM',  -- EASY, MEDIUM, HARD
                frequency_count INTEGER DEFAULT 1,
                last_appeared_year INTEGER,
                paper_id INTEGER NOT NULL,
                subject VARCHAR(50) NOT NULL,
                board VARCHAR(20) NOT NULL,
                course VARCHAR(10),
                class_level VARCHAR(10) NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paper_id) REFERENCES question_papers(id)
            )
        ''')
        
        # Payments table (mock payments)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id VARCHAR(50) UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                payment_type VARCHAR(20) DEFAULT 'PDF_DOWNLOAD',
                status VARCHAR(20) DEFAULT 'SUCCESS',
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Downloads table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                download_type VARCHAR(30) NOT NULL,  -- PREVIOUS_YEAR, GENERATED_PAPER
                subject VARCHAR(50) NOT NULL,
                difficulty VARCHAR(10),
                file_path VARCHAR(500),
                download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_free_download BOOLEAN DEFAULT FALSE,
                payment_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (payment_id) REFERENCES payments(id)
            )
        ''')
        
        # User sessions (to track separate free downloads)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                prev_year_downloads INTEGER DEFAULT 0,
                practice_downloads INTEGER DEFAULT 0,
                last_reset_date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        
        # Insert default admin if not exists
        self.create_default_admin()
        
        print("Database initialized successfully!")
    
    def create_default_admin(self):
        """Create default admin account"""
        admin_email = "admin@prediq.com"
        admin_password = "admin123"
        admin_name = "PrediQ Administrator"
        
        # Check if admin already exists
        existing_admin = self.execute_query(
            "SELECT id FROM admin WHERE email = ?", 
            (admin_email,)
        )
        
        if not existing_admin:
            password_hash = self.hash_password(admin_password)
            self.execute_update(
                "INSERT INTO admin (email, password_hash, full_name) VALUES (?, ?, ?)",
                (admin_email, password_hash, admin_name)
            )
            print(f"Default admin created: {admin_email} / {admin_password}")
    
    # User management methods
    def create_user(self, username: str, email: str, password: str, full_name: str, phone: str = None) -> bool:
        """Create a new student user"""
        try:
            password_hash = self.hash_password(password)
            self.execute_update(
                "INSERT INTO users (username, email, password_hash, full_name, phone) VALUES (?, ?, ?, ?, ?)",
                (username, email, password_hash, full_name, phone)
            )
            
            # Create user session record
            user_id = self.execute_query("SELECT last_insert_rowid()")[0][0]
            self.execute_update(
                "INSERT INTO user_sessions (user_id) VALUES (?)",
                (user_id,)
            )
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate_user(self, username_or_email: str, password: str) -> Optional[Dict]:
        """Authenticate student user by username or email"""
        password_hash = self.hash_password(password)
        result = self.execute_query(
            "SELECT id, username, email, full_name FROM users WHERE (username = ? OR email = ?) AND password_hash = ? AND is_active = TRUE",
            (username_or_email, username_or_email, password_hash)
        )
        return dict(result[0]) if result else None
    
    def authenticate_admin(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate admin user"""
        password_hash = self.hash_password(password)
        result = self.execute_query(
            "SELECT id, email, full_name FROM admin WHERE email = ? AND password_hash = ?",
            (email, password_hash)
        )
        return dict(result[0]) if result else None
    
    # Question paper methods
    def add_question_paper(self, title: str, year: int, board: str, course: str, 
                          subject: str, class_level: str, file_path: str, uploaded_by: int) -> int:
        """Add a new question paper"""
        result = self.execute_update(
            """INSERT INTO question_papers (title, year, board, course, subject, class_level, file_path, uploaded_by) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, year, board, course, subject, class_level, file_path, uploaded_by)
        )
        return self.execute_query("SELECT last_insert_rowid()")[0][0]
    
    def get_question_papers(self, board: str = None, subject: str = None, class_level: str = None) -> List[Dict]:
        """Get question papers with optional filters"""
        query = "SELECT * FROM question_papers WHERE 1=1"
        params = []
        
        if board:
            query += " AND board = ?"
            params.append(board)
        if subject:
            query += " AND subject = ?"
            params.append(subject)
        if class_level:
            query += " AND class_level = ?"
            params.append(class_level)
        
        query += " ORDER BY year DESC"
        
        result = self.execute_query(query, tuple(params))
        return [dict(row) for row in result]
    
    # Question methods
    def add_question(self, question_text: str, paper_id: int, subject: str, 
                    board: str, course: str, class_level: str, **kwargs) -> int:
        """Add a question from a paper"""
        return self.execute_update(
            """INSERT INTO questions (question_text, paper_id, subject, board, course, class_level,
               question_type, marks, difficulty_level, last_appeared_year) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (question_text, paper_id, subject, board, course, class_level,
             kwargs.get('question_type', 'SHORT'), kwargs.get('marks', 1),
             kwargs.get('difficulty_level', 'MEDIUM'), kwargs.get('year'))
        )
    
    def get_questions_by_subject(self, subject: str, board: str, course: str = None, 
                               class_level: str = None) -> List[Dict]:
        """Get questions for a subject"""
        query = """SELECT * FROM questions 
                   WHERE subject = ? AND board = ?"""
        params = [subject, board]
        
        if course:
            query += " AND course = ?"
            params.append(course)
        if class_level:
            query += " AND class_level = ?"
            params.append(class_level)
        
        query += " ORDER BY frequency_count DESC, last_appeared_year DESC"
        
        result = self.execute_query(query, tuple(params))
        return [dict(row) for row in result]
    
    # Payment methods
    def add_payment(self, transaction_id: str, user_id: int, amount: float, 
                   description: str = None) -> int:
        """Add a payment record"""
        return self.execute_update(
            "INSERT INTO payments (transaction_id, user_id, amount, description) VALUES (?, ?, ?, ?)",
            (transaction_id, user_id, amount, description)
        )
    
    def get_payments(self, user_id: int = None) -> List[Dict]:
        """Get payment records"""
        if user_id:
            result = self.execute_query(
                "SELECT * FROM payments WHERE user_id = ? ORDER BY payment_date DESC",
                (user_id,)
            )
        else:
            result = self.execute_query(
                """SELECT p.*, u.username, u.full_name 
                   FROM payments p 
                   JOIN users u ON p.user_id = u.id 
                   ORDER BY p.payment_date DESC"""
            )
        return [dict(row) for row in result]
    
    # Download methods
    def add_download(self, user_id: int, download_type: str, subject: str, 
                    difficulty: str = None, file_path: str = None, 
                    is_free: bool = False, payment_id: int = None) -> int:
        """Add a download record"""
        return self.execute_update(
            """INSERT INTO downloads (user_id, download_type, subject, difficulty, 
               file_path, is_free_download, payment_id) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, download_type, subject, difficulty, file_path, is_free, payment_id)
        )
    
    def get_user_downloads_count(self, user_id: int) -> int:
        """Get count of user downloads"""
        result = self.execute_query(
            "SELECT COUNT(*) FROM downloads WHERE user_id = ?",
            (user_id,)
        )
        return result[0][0] if result else 0
    
    def get_user_download_stats(self, user_id: int) -> Dict:
        """Get separate download stats for user"""
        result = self.execute_query(
            "SELECT prev_year_downloads, practice_downloads FROM user_sessions WHERE user_id = ?",
            (user_id,)
        )
        if result:
            return {
                'prev_year': result[0][0],
                'practice': result[0][1]
            }
        return {'prev_year': 0, 'practice': 0}
    
    def get_user_free_downloads_used(self, user_id: int) -> int:
        """Get count of free downloads used by user (total)"""
        stats = self.get_user_download_stats(user_id)
        return stats['prev_year'] + stats['practice']
    
    def increment_download_count(self, user_id: int, download_type: str) -> bool:
        """Increment download counter for specific type
        download_type: 'PREVIOUS_YEAR' or 'GENERATED_PAPER'
        """
        field = 'prev_year_downloads' if download_type == 'PREVIOUS_YEAR' else 'practice_downloads'
        affected = self.execute_update(
            f"UPDATE user_sessions SET {field} = {field} + 1 WHERE user_id = ?",
            (user_id,)
        )
        return affected > 0
    
    def increment_free_downloads(self, user_id: int) -> bool:
        """Increment free downloads counter for user (legacy method)"""
        # This is kept for backward compatibility, increments prev_year by default
        return self.increment_download_count(user_id, 'PREVIOUS_YEAR')
    
    def reset_free_downloads(self, user_id: int) -> bool:
        """Reset free downloads counter after payment"""
        affected = self.execute_update(
            "UPDATE user_sessions SET prev_year_downloads = 0, practice_downloads = 0 WHERE user_id = ?",
            (user_id,)
        )
        return affected > 0
    
    def get_download_logs(self) -> List[Dict]:
        """Get all download logs for admin"""
        result = self.execute_query(
            """SELECT d.*, u.username, u.full_name 
               FROM downloads d 
               JOIN users u ON d.user_id = u.id 
               ORDER BY d.download_date DESC"""
        )
        return [dict(row) for row in result]
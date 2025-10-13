import sqlite3
import os
from contextlib import contextmanager


class DatabaseManager:
    """
    Manages database connections and schema with connection pooling.
    Uses class variables to share connection across instances.
    """

    connection = None
    db_path = "data/hipaa_training.db"

    def __init__(self):
        if DatabaseManager.connection is None:
            self._init_db()

    def _init_db(self):
        """Initialize database tables if they don't exist"""
        os.makedirs("data", exist_ok=True)

        with self._get_connection() as conn:
            # Users table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Training progress table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS training_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    lesson_completed TEXT,
                    quiz_score REAL,
                    checklist_data TEXT,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Audit log table (HIPAA Requirement)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Certificates table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS certificates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    certificate_id TEXT UNIQUE NOT NULL,
                    score REAL NOT NULL,
                    issue_date TIMESTAMP,
                    expiry_date TIMESTAMP,
                    revoked BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

    @contextmanager
    def _get_connection(self):
        """Database connection context manager"""
        if DatabaseManager.connection is None:
            DatabaseManager.connection = sqlite3.connect(
                self.db_path
            )
            DatabaseManager.connection.row_factory = sqlite3.Row

        conn = DatabaseManager.connection
        try:
            yield conn
            conn.commit()
        except Exception:
            if conn:
                conn.rollback()
            raise

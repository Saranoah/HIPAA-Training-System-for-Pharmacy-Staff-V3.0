#hipaa_training/models.py
import hashlib
import json
import os
import re
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .security import (
    SecurityManager,
    ValidationError,
    SecurityError,
    RateLimitExceeded
)


class Config:
    """HIPAA-compliant configuration with validation."""
    
    DB_PATH = os.getenv('DB_URL', 'data/hipaa_training.db')
    PASS_THRESHOLD = int(os.getenv('PASS_THRESHOLD', '80'))
    TRAINING_EXPIRY_DAYS = int(os.getenv('TRAINING_EXPIRY_DAYS', '365'))
    AUDIT_RETENTION_YEARS = int(os.getenv('AUDIT_RETENTION_YEARS', '7'))
    MINI_QUIZ_THRESHOLD = int(os.getenv('MINI_QUIZ_THRESHOLD', '70'))
    
    # Rate limits
    MAX_CERT_PER_HOUR = int(os.getenv('MAX_CERT_PER_HOUR', '10'))
    MAX_USERS_PER_HOUR = int(os.getenv('MAX_USERS_PER_HOUR', '50'))
    MAX_REPORTS_PER_HOUR = int(os.getenv('MAX_REPORTS_PER_HOUR', '20'))
    
    # Security
    ENCRYPTION_KEY = os.getenv('HIPAA_ENCRYPTION_KEY')
    if not ENCRYPTION_KEY:
        raise ValueError(
            "CRITICAL: HIPAA_ENCRYPTION_KEY required! "
            "Generate: python -c 'import secrets; "
            "print(secrets.token_urlsafe(32))'"
        )
    
    # Validation patterns
    USERNAME_PATTERN = r'^[a-zA-Z0-9_.-]{3,50}$'
    ROLE_PATTERN = r'^(admin|staff|auditor)$'
    LESSON_PATTERN = r'^[a-zA-Z0-9\s\-:,.()\[\]]{1,200}$'
    
    @classmethod
    def validate(cls):
        """Validate configuration on startup."""
        if cls.PASS_THRESHOLD < 50 or cls.PASS_THRESHOLD > 100:
            raise ValueError("PASS_THRESHOLD must be 50-100")
        
        if cls.TRAINING_EXPIRY_DAYS < 1:
            raise ValueError("TRAINING_EXPIRY_DAYS must be >= 1")
        
        if cls.AUDIT_RETENTION_YEARS < 6:
            raise ValueError(
                "AUDIT_RETENTION_YEARS must be >= 6 for HIPAA compliance"
            )


class DatabaseManager:
    """
    HIPAA-compliant database manager with security hardening.
    
    Security features:
    - Encrypted sensitive data storage
    - SQL injection prevention
    - Transaction atomicity
    - Audit logging for all operations
    - Rate limiting integration
    """
    
    # Rate limiting tracking
    _cert_issuances: List[float] = []
    _user_creations: List[float] = []
    
    def __init__(self, db_path: str = Config.DB_PATH):
        self.db_path = db_path
        self.security = SecurityManager()
        self._validate_db_path()
        self._initialize_database()
        self._schedule_cleanup()
    
    def _validate_db_path(self) -> None:
        """Validate database path for security."""
        db_path = Path(self.db_path)
        
        # Prevent path traversal
        if '..' in str(db_path):
            raise SecurityError("Path traversal detected in DB_PATH")
        
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Set secure permissions on database file
        if db_path.exists():
            os.chmod(db_path, 0o600)
    
    def _initialize_database(self) -> None:
        """Initialize database with comprehensive schema."""
        with self._get_connection() as conn:
            # Enable foreign keys and WAL mode
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            
            # Users table with password support
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    password_hash TEXT,
                    role TEXT NOT NULL CHECK(role IN ('admin','staff','auditor')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    CONSTRAINT valid_username CHECK(
                        length(username) >= 3 AND length(username) <= 50
                    ),
                    CONSTRAINT valid_name CHECK(length(full_name) > 0)
                )
            '' ''

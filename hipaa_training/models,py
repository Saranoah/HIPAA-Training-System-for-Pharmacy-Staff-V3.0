# hipaa_training/models.py
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
import json
from typing import Dict, Optional
from .security import SecurityManager


class Config:
    """Configuration class for HIPAA Training System"""
    DB_PATH = os.getenv('DB_URL', 'data/hipaa_training.db')
    PASS_THRESHOLD = int(os.getenv('PASS_THRESHOLD', '80'))
    TRAINING_EXPIRY_DAYS = int(os.getenv('TRAINING_EXPIRY_DAYS', '365'))
    AUDIT_RETENTION_YEARS = int(os.getenv('AUDIT_RETENTION_YEARS', '6'))
    MINI_QUIZ_THRESHOLD = int(os.getenv('MINI_QUIZ_THRESHOLD', '70'))
    
    # CRITICAL: Fail fast if encryption key not set
    ENCRYPTION_KEY = os.getenv('HIPAA_ENCRYPTION_KEY')
    if not ENCRYPTION_KEY:
        raise ValueError(
            "CRITICAL: HIPAA_ENCRYPTION_KEY environment variable must be set! "
            "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )


class DatabaseManager:
    """Manages all database operations with HIPAA-compliant audit logging"""
    
    def __init__(self, db_path: str = Config.DB_PATH):
        self.db_path = db_path
        self.security = SecurityManager()
        self._initialize_database()

    def _initialize_database(self):
        """Initialize SQLite database with necessary tables and indexes"""
        with self._get_connection() as conn:
            # Create tables
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS training_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    lesson_title TEXT,
                    quiz_score REAL,
                    checklist_data TEXT,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS certificates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    certificate_id TEXT UNIQUE NOT NULL,
                    score REAL NOT NULL,
                    issue_date TIMESTAMP NOT NULL,
                    expiry_date TIMESTAMP NOT NULL,
                    revoked BOOLEAN DEFAULT FALSE,
                    revoked_at TIMESTAMP,
                    revoked_reason TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                )
            ''')
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON training_progress(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cert_user ON certificates(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cert_expiry ON certificates(expiry_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")

    @contextmanager
    def _get_connection(self):
        """
        Get database connection as context manager with proper error handling
        
        FIXED: Added @contextmanager decorator to make this work correctly
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def save_progress(self, user_id: int, lesson_title: str, 
                     score: Optional[float], checklist_data: Optional[Dict]) -> None:
        """Save training progress with audit logging"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO training_progress (user_id, lesson_title, quiz_score, checklist_data, completed_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, lesson_title, score, 
                 json.dumps(checklist_data) if checklist_data else None, 
                 datetime.now())
            )
            self.security.log_action(user_id, "PROGRESS_SAVED", f"Lesson: {lesson_title}")

    def save_sensitive_progress(self, user_id: int, checklist_data: Dict, 
                               score: Optional[float]) -> None:
        """Save progress with encrypted sensitive data"""
        encrypted_checklist = self.security.encrypt_data(json.dumps(checklist_data))
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO training_progress (user_id, quiz_score, checklist_data, completed_at) "
                "VALUES (?, ?, ?, ?)",
                (user_id, score, encrypted_checklist, datetime.now())
            )
            self.security.log_action(user_id, "SENSITIVE_PROGRESS_SAVED", "Checklist completed")

    def issue_certificate(self, user_id: int, score: float) -> str:
        """Issue a training certificate with expiry tracking"""
        import uuid
        certificate_id = str(uuid.uuid4())
        issue_date = datetime.now()
        expiry_date = issue_date + timedelta(days=Config.TRAINING_EXPIRY_DAYS)
        
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO certificates (user_id, certificate_id, score, issue_date, expiry_date) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, certificate_id, score, issue_date, expiry_date)
            )
            self.security.log_action(
                user_id, 
                "CERTIFICATE_ISSUED", 
                f"Certificate ID: {certificate_id}, Score: {score}%, Expires: {expiry_date.date()}"
            )
        return certificate_id

    def get_compliance_stats(self) -> Dict:
        """
        Retrieve compliance statistics for reporting
        
        FIXED: Added proper handling for empty database
        """
        with self._get_connection() as conn:
            user_stats = conn.execute(
                "SELECT COUNT(*) as total_users, AVG(quiz_score) as avg_score, "
                "SUM(CASE WHEN quiz_score >= ? THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0) as pass_rate "
                "FROM training_progress WHERE quiz_score IS NOT NULL",
                (Config.PASS_THRESHOLD,)
            ).fetchone()
            
            cert_stats = conn.execute(
                "SELECT COUNT(*) as total_certs, "
                "SUM(CASE WHEN expiry_date > ? AND revoked = FALSE THEN 1 ELSE 0 END) as active_certs, "
                "SUM(CASE WHEN expiry_date <= ? THEN 1 ELSE 0 END) as expired_certs "
                "FROM certificates",
                (datetime.now(), datetime.now())
            ).fetchone()
        
        # Handle empty database case
        total_users = user_stats["total_users"] or 0
        if total_users == 0:
            return {
                "total_users": 0,
                "avg_score": 0.0,
                "pass_rate": 0.0,
                "total_certs": 0,
                "active_certs": 0,
                "expired_certs": 0
            }
        
        return {
            "total_users": total_users,
            "avg_score": round(user_stats["avg_score"] or 0, 2),
            "pass_rate": round(user_stats["pass_rate"] or 0, 2),
            "total_certs": cert_stats["total_certs"] or 0,
            "active_certs": cert_stats["active_certs"] or 0,
            "expired_certs": cert_stats["expired_certs"] or 0
        }


class UserManager:
    """Manages user creation and validation with input sanitization"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.security = SecurityManager()

    def _sanitize_input(self, input_str: str, max_length: int) -> str:
        """
        Sanitize user input to prevent XSS/script injection
        
        IMPROVED: Uses HTML escaping instead of removing all special chars
        This preserves legitimate names like O'Brien, José, etc.
        """
        import html
        sanitized = html.escape(input_str.strip())
        return sanitized[:max_length]

    def create_user(self, username: str, full_name: str, role: str) -> int:
        """Create a new user with role-based access control"""
        username = self._sanitize_input(username, 50)
        full_name = self._sanitize_input(full_name, 100)
        
        if role not in ['admin', 'staff', 'auditor']:
            raise ValueError("Invalid role. Use 'admin', 'staff', or 'auditor'.")
        
        if not username or not full_name:
            raise ValueError("Username and full name cannot be empty.")
        
        with self.db._get_connection() as conn:
            try:
                cursor = conn.execute(
                    "INSERT INTO users (username, full_name, role) VALUES (?, ?, ?)",
                    (username, full_name, role)
                )
                user_id = cursor.lastrowid
                self.security.log_action(user_id, "USER_CREATED", f"Username: {username}, Role: {role}")
                return user_id
            except sqlite3.IntegrityError:
                raise ValueError("Username already exists.")

    def user_exists(self, user_id: int) -> bool:
        """Check if user exists in database"""
        with self.db._get_connection() as conn:
            result = conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
            return bool(result)

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user details by ID"""
        with self.db._get_connection() as conn:
            result = conn.execute(
                "SELECT id, username, full_name, role, created_at FROM users WHERE id = ?", 
                (user_id,)
            ).fetchone()
            if result:
                return dict(result)
            return None


class ComplianceDashboard:
    """Generates compliance reports in multiple formats"""
    
    def __init__(self):
        self.db = DatabaseManager()

    def generate_enterprise_report(self, format_type: str) -> str:
        """
        Generate compliance report in CSV or JSON format
        
        IMPROVED: Added format validation before file creation
        """
        if format_type not in ['csv', 'json']:
            raise ValueError("Invalid format. Use 'csv' or 'json'.")
        
        stats = self.db.get_compliance_stats()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/compliance_dashboard_{timestamp}.{format_type}"
        
        os.makedirs("reports", exist_ok=True)
        
        if format_type == "csv":
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=stats.keys())
                writer.writeheader()
                writer.writerow(stats)
        else:  # json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
        
        return filename

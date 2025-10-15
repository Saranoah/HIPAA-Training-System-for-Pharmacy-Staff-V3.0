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
            ''')
            
            # Training progress with encryption
            conn.execute('''
                CREATE TABLE IF NOT EXISTS training_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    lesson_title TEXT,
                    quiz_score REAL CHECK(quiz_score >= 0 AND quiz_score <= 100),
                    checklist_data_encrypted TEXT,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    ip_address TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT valid_lesson CHECK(length(lesson_title) <= 200)
                )
            ''')
            
            # Certificates with enhanced tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS certificates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    certificate_id TEXT UNIQUE NOT NULL,
                    score REAL NOT NULL CHECK(score >= 0 AND score <= 100),
                    issue_date TIMESTAMP NOT NULL,
                    expiry_date TIMESTAMP NOT NULL,
                    revoked BOOLEAN DEFAULT FALSE,
                    revoked_at TIMESTAMP,
                    revoked_reason TEXT,
                    revoked_by INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (revoked_by) REFERENCES users(id) ON DELETE SET NULL,
                    CONSTRAINT valid_dates CHECK(expiry_date > issue_date)
                )
            ''')
            
            # Comprehensive audit log
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    session_id TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')
            
            # Performance indices
            self._create_indices(conn)
    
    def _create_indices(self, conn) -> None:
        """Create database indices for performance."""
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_user_id ON training_progress(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_lesson ON training_progress(lesson_title)",
            "CREATE INDEX IF NOT EXISTS idx_cert_user ON certificates(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_cert_expiry ON certificates(expiry_date)",
            "CREATE INDEX IF NOT EXISTS idx_cert_revoked ON certificates(revoked)",
            "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)",
            "CREATE INDEX IF NOT EXISTS idx_username ON users(username)",
        ]
        
        for index_sql in indices:
            conn.execute(index_sql)
    
    @contextmanager
    def _get_connection(self):
        """
        Secure database connection with transaction management.
        
        Features:
        - Automatic commit on success
        - Rollback on errors
        - Row factory for dict access
        - Connection pooling ready
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            
            yield conn
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def _check_rate_limit(self, operation: str) -> None:
        """Check rate limits for database operations."""
        current_time = time.time()
        window_start = current_time - 3600  # 1 hour
        
        if operation == "certificate":
            attempts = self._cert_issuances
            limit = Config.MAX_CERT_PER_HOUR
        elif operation == "user":
            attempts = self._user_creations
            limit = Config.MAX_USERS_PER_HOUR
        else:
            return
        
        # Clean old attempts
        attempts[:] = [t for t in attempts if t > window_start]
        
        if len(attempts) >= limit:
            raise RateLimitExceeded(f"{operation} rate limit exceeded")
        
        attempts.append(current_time)
    
    def save_progress(
        self,
        user_id: int,
        lesson_title: str,
        score: Optional[float],
        checklist_data: Optional[Dict],
        session_id: str = "SYSTEM",
        ip_address: str = "127.0.0.1"
    ) -> None:
        """
        Save training progress with encryption and validation.
        
        Args:
            user_id: User identifier
            lesson_title: Lesson name (validated)
            score: Quiz score (0-100)
            checklist_data: Checklist responses (encrypted)
            session_id: Session identifier
            ip_address: Client IP
            
        Raises:
            ValidationError: Input validation failure
            SecurityError: Encryption failure
        """
        # Validate inputs
        user_id = int(user_id)
        
        if lesson_title:
            lesson_title = self.security.validate_input(
                lesson_title,
                "lesson_title",
                max_length=200,
                pattern=Config.LESSON_PATTERN,
                context="html"
            )
        
        if score is not None:
            if not 0 <= score <= 100:
                raise ValidationError("Score must be 0-100")
        
        # Encrypt checklist data
        encrypted_checklist = None
        if checklist_data:
            try:
                encrypted_checklist = self.security.encrypt_data(
                    json.dumps(checklist_data, ensure_ascii=False)
                )
            except Exception as e:
                raise SecurityError(f"Checklist encryption failed: {e}")
        
        # Save to database
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO training_progress 
                    (user_id, lesson_title, quiz_score, 
                     checklist_data_encrypted, session_id, 
                     ip_address, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        lesson_title,
                        score,
                        encrypted_checklist,
                        session_id,
                        ip_address,
                        datetime.now()
                    )
                )
            
            # Audit logging
            self.security.log_action(
                user_id=user_id,
                action="PROGRESS_SAVED",
                details=f"Lesson: {lesson_title or 'N/A'}, Score: {score}",
                session_id=session_id,
                ip_address=ip_address
            )
            
        except sqlite3.Error as e:
            self.security.log_action(
                user_id=user_id,
                action="PROGRESS_SAVE_FAILED",
                details=f"Error: {str(e)}",
                session_id=session_id,
                ip_address=ip_address
            )
            raise SecurityError(f"Failed to save progress: {e}")
    
    def save_sensitive_progress(
        self,
        user_id: int,
        checklist_data: Dict,
        score: Optional[float],
        session_id: str = "SYSTEM",
        ip_address: str = "127.0.0.1"
    ) -> None:
        """Save progress with mandatory encryption."""
        self.save_progress(
            user_id=user_id,
            lesson_title=None,
            score=score,
            checklist_data=checklist_data,
            session_id=session_id,
            ip_address=ip_address
        )
    
    def issue_certificate(
        self,
        user_id: int,
        score: float,
        session_id: str = "SYSTEM",
        ip_address: str = "127.0.0.1"
    ) -> str:
        """
        Issue training certificate with rate limiting.
        
        Args:
            user_id: User identifier
            score: Final score (validated)
            session_id: Session identifier
            ip_address: Client IP
            
        Returns:
            Certificate UUID
            
        Raises:
            RateLimitExceeded: Too many certificates
            ValidationError: Invalid score
        """
        # Rate limiting
        self._check_rate_limit("certificate")
        
        # Validate inputs
        user_id = int(user_id)
        if not 0 <= score <= 100:
            raise ValidationError("Score must be 0-100")
        
        # Generate secure certificate ID
        import uuid
        certificate_id = str(uuid.uuid4())
        issue_date = datetime.now()
        expiry_date = issue_date + timedelta(
            days=Config.TRAINING_EXPIRY_DAYS
        )
        
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO certificates 
                    (user_id, certificate_id, score, 
                     issue_date, expiry_date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, certificate_id, score, issue_date, expiry_date)
                )
            
            # Audit logging
            self.security.log_action(
                user_id=user_id,
                action="CERTIFICATE_ISSUED",
                details=(
                    f"ID: {certificate_id}, Score: {score}%, "
                    f"Expires: {expiry_date.date()}"
                ),
                session_id=session_id,
                ip_address=ip_address
            )
            
            return certificate_id
            
        except sqlite3.Error as e:
            self.security.log_action(
                user_id=user_id,
                action="CERTIFICATE_ISSUE_FAILED",
                details=f"Error: {str(e)}",
                session_id=session_id,
                ip_address=ip_address
            )
            raise SecurityError(f"Certificate issuance failed: {e}")
    
    def get_compliance_stats(self) -> Dict:
        """Retrieve compliance statistics with safe aggregation."""
        try:
            with self._get_connection() as conn:
                # User statistics
                user_stats = conn.execute(
                    """
                    SELECT 
                        COUNT(*) as total_users,
                        COALESCE(AVG(quiz_score), 0) as avg_score,
                        COALESCE(
                            SUM(CASE WHEN quiz_score >= ? THEN 1 ELSE 0 END) 
                            * 100.0 / NULLIF(COUNT(*), 0),
                            0
                        ) as pass_rate
                    FROM training_progress 
                    WHERE quiz_score IS NOT NULL
                    """,
                    (Config.PASS_THRESHOLD,)
                ).fetchone()
                
                # Certificate statistics
                cert_stats = conn.execute(
                    """
                    SELECT 
                        COUNT(*) as total_certs,
                        SUM(CASE 
                            WHEN expiry_date > ? AND revoked = FALSE 
                            THEN 1 ELSE 0 
                        END) as active_certs,
                        SUM(CASE 
                            WHEN expiry_date <= ? 
                            THEN 1 ELSE 0 
                        END) as expired_certs
                    FROM certificates
                    """,
                    (datetime.now(), datetime.now())
                ).fetchone()
            
            return {
                "total_users": user_stats["total_users"] or 0,
                "avg_score": round(user_stats["avg_score"] or 0, 2),
                "pass_rate": round(user_stats["pass_rate"] or 0, 2),
                "total_certs": cert_stats["total_certs"] or 0,
                "active_certs": cert_stats["active_certs"] or 0,
                "expired_certs": cert_stats["expired_certs"] or 0,
            }
            
        except sqlite3.Error as e:
            self.security.log_action(
                user_id=0,
                action="STATS_RETRIEVAL_FAILED",
                details=f"Error: {str(e)}",
                session_id="SYSTEM",
                ip_address="127.0.0.1"
            )
            # Return safe defaults
            return {
                "total_users": 0,
                "avg_score": 0.0,
                "pass_rate": 0.0,
                "total_certs": 0,
                "active_certs": 0,
                "expired_certs": 0,
            }
    
    def _schedule_cleanup(self) -> None:
        """Schedule periodic cleanup of old audit logs."""
        # In production, implement as cron job or background task
        pass
    
    def cleanup_old_audit_logs(self) -> int:
        """
        Delete audit logs older than retention period.
        
        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.now() - timedelta(
            days=Config.AUDIT_RETENTION_YEARS * 365
        )
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM audit_log WHERE timestamp < ?",
                    (cutoff_date,)
                )
                deleted_count = cursor.rowcount
            
            self.security.log_action(
                user_id=0,
                action="AUDIT_CLEANUP",
                details=f"Deleted {deleted_count} old audit records",
                session_id="SYSTEM",
                ip_address="127.0.0.1"
            )
            
            return deleted_count
            
        except sqlite3.Error as e:
            raise SecurityError(f"Audit cleanup failed: {e}")


class UserManager:
    """
    Secure user management with input validation.
    
    Features:
    - Comprehensive input sanitization
    - Rate limiting
    - Audit logging
    - Password support (prepared for future)
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.security = SecurityManager()
    
    def create_user(
        self,
        username: str,
        full_name: str,
        role: str,
        session_id: str = "SYSTEM",
        ip_address: str = "127.0.0.1"
    ) -> int:
        """
        Create new user with validation.
        
        Args:
            username: Username (validated against pattern)
            full_name: Full name (sanitized)
            role: User role (admin/staff/auditor)
            session_id: Session identifier
            ip_address: Client IP
            
        Returns:
            User ID
            
        Raises:
            ValidationError: Invalid input
            RateLimitExceeded: Too many user creations
        """
        # Rate limiting
        self.db._check_rate_limit("user")
        
        # Validate username
        username = self.security.validate_input(
            username,
            "username",
            max_length=50,
            pattern=Config.USERNAME_PATTERN,
            context="html"
        )
        
        # Validate full name
        full_name = self.security.validate_input(
            full_name,
            "full_name",
            max_length=100,
            context="html"
        )
        
        # Validate role
        if not re.match(Config.ROLE_PATTERN, role):
            raise ValidationError(
                "Invalid role. Must be: admin, staff, or auditor"
            )
        
        try:
            with self.db._get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO users (username, full_name, role) 
                    VALUES (?, ?, ?)
                    """,
                    (username, full_name, role)
                )
                user_id = cursor.lastrowid
            
            # Audit logging
            self.security.log_action(
                user_id=user_id,
                action="USER_CREATED",
                details=f"Username: {username}, Role: {role}",
                session_id=session_id,
                ip_address=ip_address
            )
            
            return user_id
            
        except sqlite3.IntegrityError as e:
            # Log failed attempt (don't leak username info)
            self.security.log_action(
                user_id=0,
                action="USER_CREATE_FAILED",
                details="Username conflict",
                session_id=session_id,
                ip_address=ip_address
            )
            raise ValidationError("Username already exists or invalid")
    
    def user_exists(self, user_id: int) -> bool:
        """Check if user exists (safe query)."""
        try:
            user_id = int(user_id)
            with self.db._get_connection() as conn:
                result = conn.execute(
                    "SELECT 1 FROM users WHERE id = ? LIMIT 1",
                    (user_id,)
                ).fetchone()
                return bool(result)
        except (ValueError, sqlite3.Error):
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """
        Get user details (safe retrieval).
        
        Args:
            user_id: User identifier
            
        Returns:
            User dict or None
        """
        try:
            user_id = int(user_id)
            with self.db._get_connection() as conn:
                result = conn.execute(
                    """
                    SELECT id, username, full_name, role, created_at 
                    FROM users 
                    WHERE id = ? 
                    LIMIT 1
                    """,
                    (user_id,)
                ).fetchone()
                
                if result:
                    return dict(result)
                return None
                
        except (ValueError, sqlite3.Error) as e:
            self.security.log_action(
                user_id=0,
                action="USER_RETRIEVAL_FAILED",
                details=f"Error: {str(e)}",
                session_id="SYSTEM",
                ip_address="127.0.0.1"
            )
            return None


class ComplianceDashboard:
    """
    Secure compliance reporting with path validation.
    
    Features:
    - Path traversal prevention
    - Format validation
    - Rate limiting
    - Audit logging
    """
    
    # Rate limiting tracking
    _report_generations: List[float] = []
    
    def __init__(self):
        self.db = DatabaseManager()
        self.security = SecurityManager()
    
    def _check_rate_limit(self) -> None:
        """Check report generation rate limit."""
        current_time = time.time()
        window_start = current_time - 3600  # 1 hour
        
        # Clean old attempts
        self._report_generations[:] = [
            t for t in self._report_generations if t > window_start
        ]
        
        if len(self._report_generations) >= Config.MAX_REPORTS_PER_HOUR:
            raise RateLimitExceeded("Report generation rate limit exceeded")
        
        self._report_generations.append(current_time)
    
    def generate_enterprise_report(
        self,
        format_type: str,
        session_id: str = "SYSTEM",
        ip_address: str = "127.0.0.1"
    ) -> str:
        """
        Generate compliance report with security validation.
        
        Args:
            format_type: Report format (csv or json only)
            session_id: Session identifier
            ip_address: Client IP
            
        Returns:
            Safe filename path
            
        Raises:
            ValidationError: Invalid format
            RateLimitExceeded: Too many reports
        """
        # Rate limiting
        self._check_rate_limit()
        
        # Validate format (strict whitelist)
        if format_type not in ['csv', 'json']:
            raise ValidationError("Format must be 'csv' or 'json'")
        
        # Get statistics
        stats = self.db.get_compliance_stats()
        
        # Generate safe filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_format = re.sub(r'[^a-z]', '', format_type.lower())
        base_name = f"compliance_dashboard_{timestamp}.{safe_format}"
        
        # Validate base_name doesn't contain path traversal
        if '..' in base_name or '/' in base_name or '\\' in base_name:
            raise SecurityError("Invalid filename detected")
        
        # Create reports directory securely
        reports_dir = Path("reports")
        reports_dir.mkdir(mode=0o750, parents=True, exist_ok=True)
        
        # Construct safe absolute path
        filename = reports_dir / base_name
        filename = filename.resolve()
        
        # Ensure file is within reports directory
        if not str(filename).startswith(str(reports_dir.resolve())):
            raise SecurityError("Path traversal attempt detected")
        
        try:
            # Generate report
            if format_type == "csv":
                self._write_csv_report(filename, stats)
            else:
                self._write_json_report(filename, stats)
            
            # Set secure file permissions
            os.chmod(filename, 0o640)
            
            # Audit logging
            self.security.log_action(
                user_id=0,
                action="REPORT_GENERATED",
                details=f"Format: {format_type}, File: {base_name}",
                session_id=session_id,
                ip_address=ip_address
            )
            
            return str(filename)
            
        except Exception as e:
            self.security.log_action(
                user_id=0,
                action="REPORT_GENERATION_FAILED",
                details=f"Error: {str(e)}",
                session_id=session_id,
                ip_address=ip_address
            )
            raise SecurityError(f"Report generation failed: {e}")
    
    def _write_csv_report(self, filename: Path, stats: Dict) -> None:
        """Write CSV report with safe handling."""
        import csv
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                # Sanitize field names for CSV injection prevention
                safe_fields = [
                    self.security.validate_input(
                        str(k), 
                        'field_name',
                        max_length=50,
                        context='html'
                    )
                    for k in stats.keys()
                ]
                
                writer = csv.DictWriter(
                    f, 
                    fieldnames=list(stats.keys()),
                    quoting=csv.QUOTE_ALL  # Prevent CSV injection
                )
                writer.writeheader()
                
                # Sanitize values
                safe_row = {}
                for key, value in stats.items():
                    # Prevent formula injection
                    if isinstance(value, str):
                        value = self.security.validate_input(
                            value,
                            'csv_value',
                            max_length=1000,
                            context='html'
                        )
                        # Remove leading special chars that could be formulas
                        if value and value[0] in ['=', '+', '-', '@']:
                            value = "'" + value
                    safe_row[key] = value
                
                writer.writerow(safe_row)
                
        except IOError as e:
            raise SecurityError(f"CSV write failed: {e}")
    
    def _write_json_report(self, filename: Path, stats: Dict) -> None:
        """Write JSON report with safe serialization."""
        try:
            # Sanitize all string values
            safe_stats = {}
            for key, value in stats.items():
                if isinstance(value, str):
                    value = self.security.validate_input(
                        value,
                        'json_value',
                        max_length=1000,
                        context='html'
                    )
                safe_stats[key] = value
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(
                    safe_stats,
                    f,
                    indent=2,
                    ensure_ascii=False,
                    sort_keys=True
                )
                
        except (IOError, json.JSONEncodeError) as e:
            raise SecurityError(f"JSON write failed: {e}")


# Configuration validation on module import
try:
    Config.validate()
except ValueError as e:
    print(f"❌ CONFIGURATION ERROR: {e}")
    exit(1)

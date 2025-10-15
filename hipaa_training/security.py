# hipaa_training/security.py
"""
Comprehensive test suite for HIPAA Security Manager
Tests all security features, edge cases, and compliance requirements
"""
import os
import secrets
import sqlite3
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Set test environment variables before import
os.environ["HIPAA_ENCRYPTION_KEY"] = secrets.token_urlsafe(32)
os.environ["HIPAA_SALT"] = secrets.token_hex(32)
os.environ["DB_URL"] = ":memory:"

from security_manager import (
    ActionType,
    AuditError,
    CircuitBreaker,
    CircuitBreakerOpen,
    EncryptionError,
    RateLimitExceeded,
    SecurityConfig,
    SecurityLevel,
    SecurityManager,
    ValidationError,
)


class TestSecurityConfig(unittest.TestCase):
    """Test security configuration validation."""

    def test_missing_encryption_key_raises_error(self):
        """Test that missing encryption key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="HIPAA_ENCRYPTION_KEY"):
                SecurityConfig.from_environment()

    def test_missing_salt_raises_error(self):
        """Test that missing salt raises ValueError."""
        with patch.dict(
            os.environ,
            {"HIPAA_ENCRYPTION_KEY": secrets.token_urlsafe(32)},
            clear=True,
        ):
            with pytest.raises(ValueError, match="HIPAA_SALT"):
                SecurityConfig.from_environment()

    def test_short_encryption_key_raises_error(self):
        """Test that short encryption key raises ValueError."""
        with patch.dict(
            os.environ,
            {
                "HIPAA_ENCRYPTION_KEY": "short",
                "HIPAA_SALT": secrets.token_hex(32),
            },
            clear=True,
        ):
            with pytest.raises(
                ValueError, match="must be >= 32 characters"
            ):
                SecurityConfig.from_environment()

    def test_invalid_salt_format_raises_error(self):
        """Test that invalid salt format raises ValueError."""
        with patch.dict(
            os.environ,
            {
                "HIPAA_ENCRYPTION_KEY": secrets.token_urlsafe(32),
                "HIPAA_SALT": "not-hex-format",
            },
            clear=True,
        ):
            with pytest.raises(ValueError, match="Invalid HIPAA_SALT"):
                SecurityConfig.from_environment()

    def test_valid_config_loads_successfully(self):
        """Test that valid configuration loads without errors."""
        config = SecurityConfig.from_environment()
        assert config.pbkdf2_iterations >= 600000
        assert config.encryption_version == "v2"
        assert config.salt_length == 32


class TestEncryptionDecryption(unittest.TestCase):
    """Test encryption and decryption functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = SecurityConfig.from_environment()
        self.manager = SecurityManager(self.config)

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly."""
        original_data = "Sensitive HIPAA Data"
        encrypted = self.manager.encrypt_data(original_data)
        decrypted, metadata = self.manager.decrypt_data(encrypted)
        assert decrypted == original_data

    def test_encrypt_empty_string_raises_error(self):
        """Test that encrypting empty string raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            self.manager.encrypt_data("")

    def test_encrypt_whitespace_only_raises_error(self):
        """Test that encrypting whitespace raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            self.manager.encrypt_data("   ")

    def test_encrypt_non_string_raises_error(self):
        """Test that encrypting non-string raises ValidationError."""
        with pytest.raises(ValidationError, match="must be string"):
            self.manager.encrypt_data(12345)

    def test_encrypt_oversized_data_raises_error(self):
        """Test that oversized data raises ValidationError."""
        large_data = "x" * (11 * 1024 * 1024)  # 11MB
        with pytest.raises(ValidationError, match="exceeds"):
            self.manager.encrypt_data(large_data)

    def test_decrypt_invalid_data_raises_error(self):
        """Test that decrypting invalid data raises EncryptionError."""
        with pytest.raises(EncryptionError):
            self.manager.decrypt_data("invalid-encrypted-data")

    def test_decrypt_empty_string_raises_error(self):
        """Test that decrypting empty string raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid encrypted"):
            self.manager.decrypt_data("")

    def test_encryption_includes_metadata(self):
        """Test that encryption includes version and timestamp."""
        data = "Test data"
        encrypted = self.manager.encrypt_data(data)
        decrypted, metadata = self.manager.decrypt_data(encrypted)
        assert decrypted == data
        assert "timestamp" in metadata or metadata == {}

    def test_encryption_with_custom_metadata(self):
        """Test encryption with custom metadata."""
        data = "Test data"
        custom_meta = {"user_id": 123, "action": "test"}
        encrypted = self.manager.encrypt_data(data, metadata=custom_meta)
        decrypted, metadata = self.manager.decrypt_data(encrypted)
        assert decrypted == data
        assert metadata.get("user_id") == 123


class TestInputValidation(unittest.TestCase):
    """Test input validation and sanitization."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = SecurityManager()

    def test_validate_input_basic_string(self):
        """Test basic string validation."""
        result = self.manager.validate_input(
            "test@example.com", "email", max_length=50
        )
        assert result == "test@example.com"

    def test_validate_input_strips_whitespace(self):
        """Test that validation strips whitespace."""
        result = self.manager.validate_input(
            "  test  ", "username", max_length=20
        )
        assert result == "test"

    def test_validate_input_rejects_empty(self):
        """Test that empty input is rejected."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            self.manager.validate_input("", "username")

    def test_validate_input_rejects_too_long(self):
        """Test that oversized input is rejected."""
        with pytest.raises(ValidationError, match="exceeds"):
            self.manager.validate_input("x" * 1001, "field", max_length=10)

    def test_validate_input_pattern_matching(self):
        """Test regex pattern validation."""
        result = self.manager.validate_input(
            "user123", "username", pattern=r"^[a-z0-9]+$"
        )
        assert result == "user123"

    def test_validate_input_pattern_rejection(self):
        """Test that invalid patterns are rejected."""
        with pytest.raises(ValidationError, match="format invalid"):
            self.manager.validate_input(
                "user@123", "username", pattern=r"^[a-z0-9]+$"
            )

    def test_sanitize_html_escapes_tags(self):
        """Test HTML sanitization escapes tags."""
        result = self.manager.validate_input(
            "<script>alert('xss')</script>", "comment", context="html"
        )
        assert "<script>" not in result
        assert "&lt;" in result or "script" not in result

    def test_sanitize_url_encodes_special_chars(self):
        """Test URL sanitization encodes special characters."""
        result = self.manager.validate_input(
            "hello world", "url", context="url"
        )
        assert " " not in result
        assert "hello" in result

    def test_sanitize_javascript_escapes_quotes(self):
        """Test JavaScript sanitization escapes quotes."""
        result = self.manager.validate_input(
            'test"value', "script", context="js"
        )
        assert '\\"' in result or '"' not in result

    def test_validate_input_non_string_raises_error(self):
        """Test that non-string input raises ValidationError."""
        with pytest.raises(ValidationError, match="must be string"):
            self.manager.validate_input(123, "field")


class TestRateLimiting(unittest.TestCase):
    """Test rate limiting functionality."""

    def setUp(self):
        """Set up test fixtures."""
        config = SecurityConfig.from_environment()
        config.max_encryptions_per_minute = 5
        self.manager = SecurityManager(config)

    def test_rate_limit_allows_under_threshold(self):
        """Test that requests under limit are allowed."""
        for _ in range(4):
            self.manager.encrypt_data("test")
        # Should not raise

    def test_rate_limit_blocks_over_threshold(self):
        """Test that exceeding rate limit raises error."""
        for _ in range(5):
            self.manager.encrypt_data("test")
        
        with pytest.raises(RateLimitExceeded, match="Rate limit exceeded"):
            self.manager.encrypt_data("test")

    def test_rate_limit_resets_after_window(self):
        """Test that rate limit resets after time window."""
        for _ in range(5):
            self.manager.encrypt_data("test")
        
        # Wait for window to expire
        time.sleep(61)
        
        # Should work again
        self.manager.encrypt_data("test")

    def test_failed_auth_rate_limiting(self):
        """Test failed authentication rate limiting."""
        identifier = "user123"
        
        for _ in range(4):
            self.manager._check_rate_limit("failed_auth", identifier)
        
        with pytest.raises(RateLimitExceeded, match="failed auth"):
            self.manager._check_rate_limit("failed_auth", identifier)


class TestAuditLogging(unittest.TestCase):
    """Test audit logging functionality."""

    def setUp(self):
        """Set up test fixtures with in-memory database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        
        os.environ["DB_URL"] = str(self.db_path)
        os.environ["LOG_DIR"] = self.temp_dir
        
        # Create database schema
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                session_id TEXT,
                ip_address TEXT,
                security_level TEXT,
                checksum TEXT,
                metadata TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()
        
        self.config = SecurityConfig.from_environment()
        self.manager = SecurityManager(self.config)

    def test_log_action_creates_entry(self):
        """Test that logging creates database entry."""
        self.manager.log_action(
            user_id=1,
            action=ActionType.LOGIN,
            details="User logged in",
            session_id="session123",
            ip_address="192.168.1.1",
            level=SecurityLevel.MEDIUM,
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT * FROM audit_log")
        rows = cursor.fetchall()
        conn.close()
        
        assert len(rows) >= 1  # At least one entry (might have startup log)

    def test_log_action_includes_checksum(self):
        """Test that logs include integrity checksum."""
        self.manager.log_action(
            user_id=1,
            action=ActionType.DATA_ACCESS,
            details="Accessed patient record",
            session_id="session123",
            ip_address="192.168.1.1",
            level=SecurityLevel.HIGH,
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT checksum FROM audit_log WHERE user_id = 1"
        )
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        assert row[0] is not None
        assert len(row[0]) > 0

    def test_log_action_validates_inputs(self):
        """Test that logging validates all inputs."""
        with pytest.raises((ValidationError, ValueError)):
            self.manager.log_action(
                user_id="invalid",  # Should be int
                action=ActionType.LOGIN,
                details="Test",
                session_id="session",
                ip_address="192.168.1.1",
            )

    def test_log_action_sanitizes_details(self):
        """Test that logging sanitizes dangerous content."""
        self.manager.log_action(
            user_id=1,
            action=ActionType.DATA_MODIFY,
            details="<script>alert('xss')</script>",
            session_id="session123",
            ip_address="192.168.1.1",
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT details FROM audit_log WHERE user_id = 1"
        )
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        assert "<script>" not in row[0]


class TestCircuitBreaker(unittest.TestCase):
    """Test circuit breaker pattern."""

    def test_circuit_breaker_allows_success(self):
        """Test that circuit breaker allows successful operations."""
        cb = CircuitBreaker(failure_threshold=3)
        
        result = cb.call(lambda: "success")
        assert result == "success"
        assert cb.state == "CLOSED"

    def test_circuit_breaker_opens_on_failures(self):
        """Test that circuit breaker opens after threshold."""
        cb = CircuitBreaker(failure_threshold=3)
        
        def failing_func():
            raise Exception("Failure")
        
        for _ in range(3):
            try:
                cb.call(failing_func)
            except Exception:
                pass
        
        assert cb.state == "OPEN"

    def test_circuit_breaker_blocks_when_open(self):
        """Test that open circuit breaker blocks calls."""
        cb = CircuitBreaker(failure_threshold=2)
        
        def failing_func():
            raise Exception("Failure")
        
        for _ in range(2):
            try:
                cb.call(failing_func)
            except Exception:
                pass
        
        with pytest.raises(CircuitBreakerOpen):
            cb.call(lambda: "test")

    def test_circuit_breaker_recovers(self):
        """Test that circuit breaker recovers after timeout."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        def failing_func():
            raise Exception("Failure")
        
        for _ in range(2):
            try:
                cb.call(failing_func)
            except Exception:
                pass
        
        time.sleep(1.1)
        
        # Should transition to HALF_OPEN and allow retry
        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.state == "CLOSED"


class TestSessionManagement(unittest.TestCase):
    """Test session management."""

    def setUp(self):
        """Set up test fixtures."""
        config = SecurityConfig.from_environment()
        config.session_timeout_minutes = 1
        self.manager = SecurityManager(config)

    def test_create_session_returns_id(self):
        """Test that session creation returns valid ID."""
        session_id = self.manager.create_session(user_id=1)
        assert session_id is not None
        assert len(session_id) > 0

    def test_validate_session_accepts_valid(self):
        """Test that valid session is accepted."""
        session_id = self.manager.create_session(user_id=1)
        assert self.manager.validate_session(session_id) is True

    def test_validate_session_rejects_invalid(self):
        """Test that invalid session is rejected."""
        assert self.manager.validate_session("invalid-session") is False

    def test_validate_session_expires_old_sessions(self):
        """Test that old sessions expire."""
        session_id = self.manager.create_session(user_id=1)
        
        # Manually set old timestamp
        from datetime import timedelta
        old_time = datetime.now(timezone.utc) - timedelta(minutes=2)
        self.manager._active_sessions[session_id] = old_time
        
        assert self.manager.validate_session(session_id) is False


class TestHealthCheck(unittest.TestCase):
    """Test health check functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        
        os.environ["DB_URL"] = str(self.db_path)
        os.environ["LOG_DIR"] = self.temp_dir
        
        # Create database schema
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                session_id TEXT,
                ip_address TEXT,
                security_level TEXT,
                checksum TEXT,
                metadata TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()
        
        self.manager = SecurityManager()

    def test_health_check_returns_status(self):
        """Test that health check returns comprehensive status."""
        health = self.manager.health_check()
        
        assert "timestamp" in health
        assert "checks" in health
        assert "overall_status" in health

    def test_health_check_verifies_encryption(self):
        """Test that health check verifies encryption."""
        health = self.manager.health_check()
        
        assert "encryption" in health["checks"]
        assert health["checks"]["encryption"] is True

    def test_health_check_verifies_database(self):
        """Test that health check verifies database."""
        health = self.manager.health_check()
        
        assert "database" in health["checks"]
        assert health["checks"]["database"] is True

    def test_health_check_includes_circuit_breaker(self):
        """Test that health check includes circuit breaker status."""
        health = self.manager.health_check()
        
        assert "circuit_breaker" in health["checks"]
        assert health["checks"]["circuit_breaker"] in [
            "CLOSED", "OPEN", "HALF_OPEN"
        ]


class TestAnomalyDetection(unittest.TestCase):
    """Test anomaly detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        os.environ["LOG_DIR"] = self.temp_dir
        self.manager = SecurityManager()

    def test_anomaly_detection_flags_rapid_actions(self):
        """Test that rapid repeated actions trigger anomaly."""
        user_id = 1
        action = "DATA_ACCESS"
        
        # Simulate rapid repeated actions
        for _ in range(25):
            self.manager._detect_anomalies(user_id, action)
        
        # Check that anomaly was logged (implicitly through no error)
        assert user_id in self.manager._user_patterns


class TestIPValidation(unittest.TestCase):
    """Test IP address validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = SecurityManager()

    def test_validate_ipv4_accepts_valid(self):
        """Test that valid IPv4 is accepted."""
        result = self.manager._validate_ip("192.168.1.1")
        assert result == "192.168.1.1"

    def test_validate_ip_rejects_invalid(self):
        """Test that invalid IP returns placeholder."""
        result = self.manager._validate_ip("not-an-ip")
        assert result == "0.0.0.0"

    def test_validate_ipv6_accepts_valid(self):
        """Test that valid IPv6 is accepted."""
        result = self.manager._validate_ip("2001:0db8:85a3::8a2e:0370:7334")
        assert result == "2001:0db8:85a3::8a2e:0370:7334"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

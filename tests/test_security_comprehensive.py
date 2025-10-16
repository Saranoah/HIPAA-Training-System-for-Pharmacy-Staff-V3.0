#test_security_comprehensive.py
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

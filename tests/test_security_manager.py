# tests/test_security_manager.py
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

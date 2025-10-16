# hipaa_training/security.py
import base64
import hashlib
import hmac
import json
import logging
import os
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecurityLevel(Enum):
    """Security levels for operations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionType(Enum):
    """Valid audit log action types."""
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    DATA_ACCESS = "DATA_ACCESS"
    DATA_MODIFY = "DATA_MODIFY"
    DATA_DELETE = "DATA_DELETE"
    ENCRYPTION = "ENCRYPTION"
    DECRYPTION = "DECRYPTION"
    KEY_ROTATION = "KEY_ROTATION"
    HEALTH_CHECK = "HEALTH_CHECK"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    AUDIT_FAILURE = "AUDIT_FAILURE"


@dataclass
class SecurityConfig:
    """Immutable security configuration with validation."""

    # Encryption settings (OWASP 2024)
    pbkdf2_iterations: int
    encryption_version: str
    salt_length: int
    key_rotation_days: int

    # Rate limiting
    max_encryptions_per_minute: int
    max_audit_logs_per_minute: int
    max_failed_auth_attempts: int

    # Database
    db_path: str
    db_timeout: float
    db_max_connections: int

    # Logging
    log_dir: Path
    max_log_size: int
    log_backup_count: int
    log_retention_days: int

    # Security thresholds
    max_data_size: int
    max_field_length: int
    session_timeout_minutes: int

    # Secrets
    encryption_key: str
    salt: str

    @classmethod
    def from_environment(cls) -> "SecurityConfig":
        """Load and validate configuration from environment."""
        # Required secrets
        encryption_key = os.getenv("HIPAA_ENCRYPTION_KEY")
        salt = os.getenv("HIPAA_SALT")

        if not encryption_key:
            raise ValueError(
                "CRITICAL: HIPAA_ENCRYPTION_KEY must be set!\n"
                "Generate: python -c 'import secrets; "
                "print(secrets.token_urlsafe(32))'"
            )

        if not salt:
            raise ValueError(
                "CRITICAL: HIPAA_SALT must be set!\n"
                "Generate: python -c 'import secrets; "
                "print(secrets.token_hex(32))'"
            )

        # Validate key length
        if len(encryption_key) < 32:
            raise ValueError("HIPAA_ENCRYPTION_KEY must be >= 32 characters")

        # Validate salt format
        try:
            salt_bytes = bytes.fromhex(salt)
            if len(salt_bytes) != 32:
                raise ValueError("HIPAA_SALT must be 32 bytes (64 hex chars)")
        except ValueError as exc:
            raise ValueError(f"Invalid HIPAA_SALT format: {exc}") from exc

        return cls(
            pbkdf2_iterations=int(
                os.getenv("PBKDF2_ITERATIONS", "600000")
            ),
            encryption_version=os.getenv("ENCRYPTION_VERSION", "v2"),
            salt_length=32,
            key_rotation_days=int(os.getenv("KEY_ROTATION_DAYS", "90")),
            max_encryptions_per_minute=int(
                os.getenv("MAX_ENCRYPTIONS_PER_MINUTE", "1000")
            ),
            max_audit_audit

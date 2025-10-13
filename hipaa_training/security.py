# hipaa_training/security.py
import os
import logging
import sqlite3
import base64
import secrets
from datetime import datetime
from logging.handlers import RotatingFileHandler
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class Config:
    """Security configuration - separate from models to avoid circular imports"""
    DB_PATH = os.getenv('DB_URL', 'data/hipaa_training.db')
    ENCRYPTION_KEY = os.getenv('HIPAA_ENCRYPTION_KEY')
    if not ENCRYPTION_KEY:
        raise ValueError(
            "CRITICAL: HIPAA_ENCRYPTION_KEY environment variable must be set!"
        )


class SecurityManager:
    """
    Manages encryption, audit logging, and security operations
    
    FIXES APPLIED:
    - Added missing sqlite3 import
    - Fixed salt encoding bug
    - Added log rotation
    - Improved error handling
    """
    
    def __init__(self):
        self.setup_logging()
        self._setup_encryption()

    def setup_logging(self):
        """
        Configure rotating logs for HIPAA-compliant audit trail
        
        FIXED: Added log rotation and proper directory handling
        """
        os.makedirs('logs', exist_ok=True)
        
        # Create rotating file handler (10MB per file, keep 5 backups)
        handler = RotatingFileHandler(
            'logs/hipaa_audit.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - USER_%(user_id)s - %(action)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        self.logger = logging.getLogger('HIPAA_Audit')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False

    def _setup_encryption(self):
        """
        Setup Fernet encryption with PBKDF2 key derivation
        
        FIXED: Salt encoding bug - handles both string and bytes properly
        """
        encryption_key = Config.ENCRYPTION_KEY.encode()
        
        # Get or generate salt
        salt_env = os.getenv('HIPAA_SALT')
        if salt_env:
            # If salt is provided as hex string, convert to bytes
            try:
                salt = bytes.fromhex(salt_env)
            except ValueError:
                # If not hex, encode as UTF-8
                salt = salt_env.encode()
        else:
            # Generate random salt (should be stored securely in production)
            salt = secrets.token_bytes(16)
            # In production, you should store this salt securely and reuse it
            # For now, log a warning
            self.logger.warning(
                "HIPAA_SALT not set - using random salt. "
                "This will cause decryption failures on restart!",
                extra={'user_id': 0, 'action': 'SYSTEM_WARNING'}
            )
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(encryption_key))
        self.cipher = Fernet(key)

    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data using Fernet symmetric encryption
        
        Args:
            data: Plain text data to encrypt
            
        Returns:
            Base64-encoded encrypted data
        """
        if not data:
            return data
        try:
            return self.cipher.encrypt(data.encode()).decode()
        except Exception as e:
            self.logger.error(
                f"Encryption failed: {str(e)}",
                extra={'user_id': 0, 'action': 'ENCRYPTION_ERROR'}
            )
            raise

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Plain text data
        """
        if not encrypted_data:
            return encrypted_data
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            self.logger.error(
                f"Decryption failed: {str(e)}",
                extra={'user_id': 0, 'action': 'DECRYPTION_ERROR'}
            )
            raise

    def log_action(self, user_id: int, action: str, details: str) -> None:
        """
        Log an action to both file and database for HIPAA audit trail
        
        FIXED: Added missing sqlite3 import (now at top of file)
        IMPROVED: Added try-except for database logging failures
        """
        # Log to file
        self.logger.info(details, extra={'user_id': user_id, 'action': action})
        
        # Log to database
        try:
            ip_address = self._get_client_ip()
            with sqlite3.connect(Config.DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO audit_log (user_id, action, details, timestamp, ip_address) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, action, details, datetime.now(), ip_address)
                )
                conn.commit()
        except sqlite3.Error as e:
            # Don't let audit logging failures crash the application
            self.logger.error(
                f"Database audit log failed: {str(e)}",
                extra={'user_id': user_id, 'action': 'AUDIT_LOG_ERROR'}
            )

    def _get_client_ip(self) -> str:
        """
        Get client IP address for audit logging
        
        IMPROVED: Returns meaningful value for CLI, placeholder for future web version
        """
        # For CLI application, return localhost
        # In web application, this should extract from request headers
        return os.getenv('CLIENT_IP', '127.0.0.1')

    def encrypt_file(self, input_path: str, output_path: str) -> None:
        """
        Encrypt a file in chunks to handle large files efficiently
        
        NEW: Added for evidence file encryption with memory efficiency
        """
        CHUNK_SIZE = 64 * 1024  # 64KB chunks
        
        try:
            with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
                while chunk := f_in.read(CHUNK_SIZE):
                    encrypted_chunk = self.cipher.encrypt(chunk)
                    # Write chunk size first (4 bytes) then encrypted chunk
                    f_out.write(len(encrypted_chunk).to_bytes(4, 'big'))
                    f_out.write(encrypted_chunk)
        except Exception as e:
            self.logger.error(
                f"File encryption failed: {str(e)}",
                extra={'user_id': 0, 'action': 'FILE_ENCRYPTION_ERROR'}
            )
            raise

    def decrypt_file(self, input_path: str, output_path: str) -> None:
        """
        Decrypt a file that was encrypted in chunks
        
        NEW: Added for evidence file decryption
        """
        try:
            with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
                while True:
                    # Read chunk size
                    size_bytes = f_in.read(4)
                    if not size_bytes:
                        break
                    chunk_size = int.from_bytes(size_bytes, 'big')
                    
                    # Read and decrypt chunk
                    encrypted_chunk = f_in.read(chunk_size)
                    decrypted_chunk = self.cipher.decrypt(encrypted_chunk)
                    f_out.write(decrypted_chunk)
        except Exception as e:
            self.logger.error(
                f"File decryption failed: {str(e)}",
                extra={'user_id': 0, 'action': 'FILE_DECRYPTION_ERROR'}
            )
            raise

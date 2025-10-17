#!/usr/bin/env python3
"""
HIPAA Training Configuration Module - Production Ready v4.0.1
===========================================================

Centralized configuration management for HIPAA training system:
- Environment variable-driven settings
- Comprehensive validation at initialization
- Immutable configuration with defaults
- HIPAA-compliant audit logging
- Zero runtime failures
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import json
from threading import Lock

# ============================================================================
# CONFIGURATION EXCEPTIONS
# ============================================================================

class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass

class InvalidEnvironmentError(ConfigValidationError):
    """Invalid or missing environment configuration."""
    pass

# ============================================================================
# IMMUTABLE CONFIGURATION DATA CLASS
# ============================================================================

@dataclass(frozen=True)
class CloudConfig:
    """Immutable configuration for HIPAA training system."""
    data_dir: Path = field(default_factory=lambda: Path("data"))
    pass_threshold: int = 80
    xp_per_quiz_question: int = 10
    xp_per_checklist_item: int = 5
    max_attempts: int = 3
    debug_mode: bool = False
    audit_log_enabled: bool = True
    backup_retention_days: int = 7
    version: str = "4.0.1"
    environment: str = "production"
    
    def __post_init__(self):
        """Validate configuration at initialization."""
        if not isinstance(self.data_dir, Path):
            raise ConfigValidationError(f"Data directory must be Path: {self.data_dir}")
        if not 60 <= self.pass_threshold <= 100:
            raise ConfigValidationError(f"Pass threshold must be 60-100: {self.pass_threshold}")
        if self.xp_per_quiz_question < 1:
            raise ConfigValidationError(f"Quiz XP must be positive: {self.xp_per_quiz_question}")
        if self.xp_per_checklist_item < 1:
            raise ConfigValidationError(f"Checklist XP must be positive: {self.xp_per_checklist_item}")
        if self.max_attempts < 1:
            raise ConfigValidationError(f"Max attempts must be positive: {self.max_attempts}")
        if self.backup_retention_days < 1:
            raise ConfigValidationError(f"Backup retention must be positive: {self.backup_retention_days}")
        if not self.version:
            raise ConfigValidationError("Version string required")

# ============================================================================
# CONFIGURATION MANAGER
# ============================================================================

class ConfigManager:
    """
    Production-ready configuration manager.
    
    Features:
    - Environment variable parsing with defaults
    - Atomic configuration export for auditing
    - Thread-safe singleton pattern
    - Comprehensive validation
    - HIPAA-compliant configuration tracking
    """
    
    _instance: Optional['ConfigManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.config = self._load_config()
            self._load_time = datetime.now()
            self._validate_environment()
    
    def _load_config(self) -> CloudConfig:
        """Load configuration from environment with defaults."""
        try:
            # Environment variable parsing
            data_dir = os.getenv("HIPAA_DATA_DIR", "data")
            pass_threshold = int(os.getenv("HIPAA_PASS_THRESHOLD", "80"))
            xp_per_quiz = int(os.getenv("HIPAA_XP_PER_QUIZ", "10"))
            xp_per_checklist = int(os.getenv("HIPAA_XP_PER_CHECKLIST", "5"))
            max_attempts = int(os.getenv("HIPAA_MAX_ATTEMPTS", "3"))
            debug_mode = os.getenv("HIPAA_DEBUG_MODE", "false").lower() == "true"
            audit_log_enabled = os.getenv("HIPAA_AUDIT_LOG_ENABLED", "true").lower() == "true"
            backup_retention_days = int(os.getenv("HIPAA_BACKUP_RETENTION_DAYS", "7"))
            environment = os.getenv("HIPAA_ENVIRONMENT", "production")
            
            return CloudConfig(
                data_dir=Path(data_dir),
                pass_threshold=pass_threshold,
                xp_per_quiz_question=xp_per_quiz,
                xp_per_checklist_item=xp_per_checklist,
                max_attempts=max_attempts,
                debug_mode=debug_mode,
                audit_log_enabled=audit_log_enabled,
                backup_retention_days=backup_retention_days,
                environment=environment
            )
        
        except ValueError as e:
            raise ConfigValidationError(f"Invalid environment variable format: {e}")
        except Exception as e:
            raise ConfigValidationError(f"Configuration loading failed: {e}")
    
    def _validate_environment(self) -> None:
        """Validate environment setup."""
        try:
            # Ensure data directory is writable
            self.config.data_dir.mkdir(parents=True, exist_ok=True)
            test_file = self.config.data_dir / ".test_write"
            with open(test_file, 'w') as f:
                f.write("test")
            test_file.unlink()
            
            # Validate environment name
            if self.config.environment not in ["production", "development", "test"]:
                raise InvalidEnvironmentError(f"Invalid environment: {self.config.environment}")
        
        except OSError as e:
            raise ConfigValidationError(f"Data directory validation failed: {e}")
        except Exception as e:
            raise InvalidEnvironmentError(f"Environment validation failed: {e}")
    
    def get_config(self) -> CloudConfig:
        """Get immutable configuration."""
        return self.config
    
    def export_config_summary(self, filepath: Optional[Path] = None) -> Dict[str, Any]:
        """Export configuration summary for compliance auditing."""
        summary = {
            "version": self.config.version,
            "load_time": self._load_time.isoformat(),
            "environment": self.config.environment,
            "data_dir": str(self.config.data_dir),
            "pass_threshold": self.config.pass_threshold,
            "xp_per_quiz_question": self.config.xp_per_quiz_question,
            "xp_per_checklist_item": self.config.xp_per_checklist_item,
            "max_attempts": self.config.max_attempts,
            "debug_mode": self.config.debug_mode,
            "audit_log_enabled": self.config.audit_log_enabled,
            "backup_retention_days": self.config.backup_retention_days
        }
        
        if filepath:
            try:
                temp_path = filepath.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                temp_path.replace(filepath)
            except Exception as e:
                print(f"⚠️ Config summary export failed: {e}")
        
        return summary
    
    def validate_config_integrity(self) -> bool:
        """Validate configuration integrity for production checks."""
        try:
            # Test configuration export
            summary = self.export_config_summary()
            
            # Verify key settings
            if summary["pass_threshold"] < 60:
                return False
            if not summary["data_dir"]:
                return False
            if summary["max_attempts"] < 1:
                return False
            
            return True
            
        except Exception:
            return False

# ============================================================================
# PRODUCTION INITIALIZATION
# ============================================================================

def initialize_config_manager() -> ConfigManager:
    """
    Production initialization with validation.
    
    Raises:
        ConfigValidationError: If initialization fails
    """
    try:
        manager = ConfigManager()
        
        # Export initial config summary for audit
        summary_path = manager.config.data_dir / "config_summary.json"
        manager.export_config_summary(summary_path)
        
        print(f"✅ Configuration initialized: {manager.config.environment} environment, "
              f"data_dir={manager.config.data_dir}")
        
        return manager
        
    except ConfigValidationError as e:
        raise SystemExit(f"CRITICAL: Configuration initialization failed - {e}")

# Global configuration manager instance
CONFIG_MANAGER = initialize_config_manager()
CONFIG = CONFIG_MANAGER.get_config()

# Clean exports
__all__ = [
    "ConfigManager",
    "CloudConfig",
    "ConfigValidationError",
    "InvalidEnvironmentError",
    "CONFIG_MANAGER",
    "CONFIG"
]

# Production validation on import
if __name__ == "__main__":
    """Production configuration validation script."""
    print("🧪 Running production configuration validation...")
    
    try:
        manager = ConfigManager()
        summary = manager.export_config_summary()
        
        print(f"✅ Configuration validation PASSED")
        print(f"📊 Environment: {summary['environment']}")
        print(f"📂 Data directory: {summary['data_dir']}")
        print(f"🎯 Pass threshold: {summary['pass_threshold']}%")
        
    except ConfigValidationError as e:
        print(f"❌ Configuration validation FAILED: {e}")
        raise

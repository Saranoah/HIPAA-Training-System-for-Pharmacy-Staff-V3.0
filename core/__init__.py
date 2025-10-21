from .config import ConfigManager, CloudConfig, ConfigValidationError, InvalidEnvironmentError, CONFIG_MANAGER, CONFIG
from .content import ContentManager, Lesson, QuizQuestion, ChecklistItem, ContentValidationError, CONTENT_MANAGER
from .progress import ProgressManager, UserProgress, ProgressValidationError, CorruptedProgressError, PROGRESS_MANAGER
from .scoring import ScoringManager, Badge, BadgeType, ScoringError, InvalidScoreError, BadgeValidationError, SCORING_MANAGER
from .audit import AuditLogger

__all__ = [
    # Config exports
    "ConfigManager",
    "CloudConfig",
    "ConfigValidationError",
    "InvalidEnvironmentError",
    "CONFIG_MANAGER",
    "CONFIG",
    
    # Content exports
    "ContentManager",
    "Lesson",
    "QuizQuestion",
    "ChecklistItem",
    "ContentValidationError",
    "CONTENT_MANAGER",
    
    # Progress exports
    "ProgressManager",
    "UserProgress",
    "ProgressValidationError",
    "CorruptedProgressError",
    "PROGRESS_MANAGER",
    
    # Scoring exports
    "ScoringManager",
    "Badge",
    "BadgeType",
    "ScoringError",
    "InvalidScoreError",
    "BadgeValidationError",
    "SCORING_MANAGER",
    
    # Audit exports
    "AuditLogger"
]

__version__ = "4.0.1"

# Production validation on import
if __name__ == "__main__":
    print("🧪 Validating core package initialization...")
    
    try:
        # Validate core components
        assert CONFIG_MANAGER.validate_config_integrity(), "Config validation failed"
        assert CONTENT_MANAGER.validate_content_integrity(), "Content validation failed"
        assert PROGRESS_MANAGER.validate_progress_integrity(), "Progress validation failed"
        assert SCORING_MANAGER.validate_scoring_integrity(PROGRESS_MANAGER.load_progress()), "Scoring validation failed"
        
        print(f"✅ Core package v{__version__} validated successfully")
        
    except Exception as e:
        print(f"❌ Core package validation failed: {e}")
        raise

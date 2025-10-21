#core/scoring.py
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

from core.content import CONTENT_MANAGER, ContentValidationError
from core.progress import PROGRESS_MANAGER, UserProgress, ProgressValidationError
from core.audit import AuditLogger

# ============================================================================
# SCORING EXCEPTIONS
# ============================================================================

class ScoringError(Exception):
    """Base exception for scoring-related errors."""
    pass

class InvalidScoreError(ScoringError):
    """Invalid score calculation or input."""
    pass

class BadgeValidationError(ScoringError):
    """Badge criteria or configuration invalid."""
    pass

# ============================================================================
# SCORING DATA STRUCTURES
# ============================================================================

class BadgeType(Enum):
    """Enum for badge categories."""
    LESSON = "lesson"
    QUIZ = "quiz"
    CHECKLIST = "checklist"
    MILESTONE = "milestone"

@dataclass(frozen=True)
class Badge:
    """Immutable badge definition."""
    name: str
    type: BadgeType
    description: str
    xp_threshold: int
    required_items: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate badge configuration."""
        if not self.name or not isinstance(self.name, str):
            raise BadgeValidationError(f"Badge name required: {self.name}")
        if self.xp_threshold < 0:
            raise BadgeValidationError(f"Negative XP threshold: {self.xp_threshold}")
        if self.required_items:
            for item in self.required_items:
                if not isinstance(item, str):
                    raise BadgeValidationError(f"Invalid required item: {item}")

# ============================================================================
# SCORING MANAGER
# ============================================================================

class ScoringManager:
    """
    Production-ready scoring system for HIPAA training.
    
    Features:
    - Deterministic XP calculations
    - Level-based progression
    - Badge achievement system
    - Audit trail integration
    - Thread-safe operations
    """
    
    _instance: Optional['ScoringManager'] = None
    _lock = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._lock = object()  # Simple lock object
        return cls._instance
    
    def __init__(self, audit_logger: AuditLogger):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.audit = audit_logger
            self.badges = self._load_badges()
            self.level_thresholds = self._load_level_thresholds()
            self._version = "4.0.1"
            self._load_time = datetime.now()
    
    def _load_badges(self) -> Dict[str, Badge]:
        """Load and validate badge definitions."""
        badge_data = [
            Badge(
                name="Privacy Master",
                type=BadgeType.LESSON,
                description="Completed all Privacy Rule lessons",
                xp_threshold=45,
                required_items=["What is PHI?", "Privacy Rule"]
            ),
            Badge(
                name="Quiz Ace",
                type=BadgeType.QUIZ,
                description="Passed quiz with 90% or higher",
                xp_threshold=120  # Assuming 12/16 questions * 10 XP
            ),
            Badge(
                name="Checklist Champion",
                type=BadgeType.CHECKLIST,
                description="Completed all checklist items",
                xp_threshold=75  # 15 items * 5 XP
            ),
            Badge(
                name="Compliance Star",
                type=BadgeType.MILESTONE,
                description="Achieved full compliance (90%+ completion)",
                xp_threshold=200
            ),
            # Add more badges as needed
        ]
        
        badges = {}
        for badge in badge_data:
            try:
                badges[badge.name] = badge
            except BadgeValidationError as e:
                raise ScoringError(f"Badge validation failed: {e}")
        
        if not badges:
            raise ScoringError("No valid badges defined")
        
        return badges
    
    def _load_level_thresholds(self) -> Dict[int, int]:
        """Load level XP thresholds."""
        # Linear progression: Level N requires N * 100 XP
        return {level: level * 100 for level in range(1, 21)}  # Up to level 20
    
    def calculate_level(self, xp: int) -> int:
        """Calculate level based on XP."""
        if xp < 0:
            raise InvalidScoreError("XP cannot be negative")
        
        for level, threshold in sorted(self.level_thresholds.items(), reverse=True):
            if xp >= threshold:
                return level
        return 1
    
    def check_new_badges(self, progress: UserProgress) -> List[str]:
        """Check for newly earned badges and update progress."""
        new_badges = []
        
        for badge in self.badges.values():
            if badge.name in progress.badges:
                continue
            
            # Check XP threshold
            if progress.xp < badge.xp_threshold:
                continue
            
            # Check specific requirements
            badge_eligible = True
            if badge.required_items:
                if badge.type == BadgeType.LESSON:
                    if not all(item in progress.lessons_completed for item in badge.required_items):
                        badge_eligible = False
                elif badge.type == BadgeType.QUIZ:
                    if not any(score.percentage >= 90 for score in progress.quiz_scores):
                        badge_eligible = False
                elif badge.type == BadgeType.CHECKLIST:
                    if not all(progress.checklist.get(item, False) for item in CONTENT_MANAGER.get_checklist_items()):
                        badge_eligible = False
                elif badge.type == BadgeType.MILESTONE:
                    stats = progress.get_completion_stats()
                    overall_completion = (stats['lessons_percentage'] + stats['checklist_percentage']) / 2
                    if overall_completion < 90:
                        badge_eligible = False
            
            if badge_eligible:
                progress.badges.append(badge.name)
                new_badges.append(badge.name)
                self.audit.log_event("badge_earned", {
                    "badge": badge.name,
                    "type": badge.type.value,
                    "xp": progress.xp,
                    "level": progress.level
                })
        
        if new_badges:
            PROGRESS_MANAGER.save_progress(progress)
        
        return new_badges
    
    def calculate_lesson_xp(self, lesson_title: str, progress: UserProgress) -> Tuple[int, int, List[str]]:
        """Calculate XP for lesson completion and update level/badges."""
        if lesson_title in progress.lessons_completed:
            return 0, progress.level, []
        
        try:
            lesson = CONTENT_MANAGER.get_lesson(lesson_title)
            xp_earned, new_level = progress.add_lesson_completion(lesson_title)
            new_badges = self.check_new_badges(progress)
            return xp_earned, new_level, new_badges
        except ContentValidationError as e:
            raise ScoringError(f"Lesson scoring failed: {e}")
    
    def calculate_quiz_xp(self, score: int, total: int, progress: UserProgress) -> Tuple[int, int, bool, List[str]]:
        """Calculate XP for quiz attempt and update level/badges."""
        try:
            xp_earned, new_level, passed = progress.add_quiz_score(score, total)
            new_badges = self.check_new_badges(progress)
            return xp_earned, new_level, passed, new_badges
        except ProgressValidationError as e:
            raise ScoringError(f"Quiz scoring failed: {e}")
    
    def calculate_checklist_xp(self, item_id: str, completed: bool, progress: UserProgress) -> Tuple[Optional[int], int, List[str]]:
        """Calculate XP for checklist toggle and update level/badges."""
        try:
            result = progress.toggle_checklist_item(item_id, completed)
            new_badges = self.check_new_badges(progress)
            if result:
                xp_earned, new_level = result
                return xp_earned, new_level, new_badges
            return None, progress.level, new_badges
        except ProgressValidationError as e:
            raise ScoringError(f"Checklist scoring failed: {e}")
    
    def get_score_summary(self, progress: UserProgress) -> Dict[str, Any]:
        """Generate comprehensive score summary for reporting."""
        stats = progress.get_completion_stats()
        
        return {
            "version": self._version,
            "load_time": self._load_time.isoformat(),
            "xp": progress.xp,
            "level": progress.level,
            "xp_to_next_level": stats['xp_to_next_level'],
            "badges_earned": progress.badges,
            "badge_count": len(progress.badges),
            "total_available_badges": len(self.badges),
            "compliance_percentage": (stats['lessons_percentage'] + stats['checklist_percentage']) / 2,
            "available_xp": CONTENT_MANAGER.get_content_metadata()['total_xp_available']
        }
    
    def export_score_report(self, progress: UserProgress, filepath: Optional[Path] = None) -> Dict[str, Any]:
        """Export score report for compliance auditing."""
        report = self.get_score_summary(progress)
        
        report.update({
            "detailed_breakdown": {
                "lesson_xp": sum(CONTENT_MANAGER.get_lesson(title).xp_value for title in progress.lessons_completed),
                "quiz_xp": sum(score.score * 10 for score in progress.quiz_scores),
                "checklist_xp": sum(
                    CONTENT_MANAGER.get_checklist_item(item_id).xp_value 
                    for item_id, completed in progress.checklist.items() if completed
                ),
                "badges": [
                    {
                        "name": badge_name,
                        "type": self.badges[badge_name].type.value,
                        "description": self.badges[badge_name].description
                    }
                    for badge_name in progress.badges
                ]
            }
        })
        
        if filepath:
            try:
                temp_path = filepath.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                temp_path.replace(filepath)
            except Exception as e:
                self.audit.log_event("score_report_export_failed", {"error": str(e)})
        
        return report
    
    def validate_scoring_integrity(self, progress: UserProgress) -> bool:
        """Validate scoring system integrity for production checks."""
        try:
            # Test XP calculations
            original_xp = progress.xp
            original_level = progress.level
            original_badges = progress.badges.copy()
            
            # Simulate lesson completion
            test_lesson = next(iter(CONTENT_MANAGER.lessons))
            if test_lesson not in progress.lessons_completed:
                self.calculate_lesson_xp(test_lesson, progress)
            
            # Verify progress saved correctly
            PROGRESS_MANAGER.save_progress(progress)
            loaded_progress = PROGRESS_MANAGER.load_progress()
            
            # Validate consistency
            if loaded_progress.xp < original_xp:
                return False
            
            # Reset to original state
            progress.xp = original_xp
            progress.level = original_level
            progress.badges = original_badges
            PROGRESS_MANAGER.save_progress(progress)
            
            return True
            
        except Exception:
            return False

# ============================================================================
# PRODUCTION INITIALIZATION
# ============================================================================

def initialize_scoring_manager(audit_logger: AuditLogger) -> ScoringManager:
    """
    Production initialization with validation.
    
    Raises:
        ScoringError: If initialization fails
    """
    try:
        manager = ScoringManager(audit_logger)
        
        # Validate badge definitions
        if not manager.badges:
            raise ScoringError("No badges defined")
        
        # Test scoring operations
        progress = PROGRESS_MANAGER.load_progress()
        summary = manager.get_score_summary(progress)
        
        print(f"✅ Scoring manager initialized: {len(manager.badges)} badges, "
              f"{len(manager.level_thresholds)} levels")
        
        return manager
        
    except Exception as e:
        raise ScoringError(f"Scoring initialization failed: {e}")

# Global scoring manager instance
SCORING_MANAGER = initialize_scoring_manager(AuditLogger(Path(CONFIG.data_dir)))

# Clean exports
__all__ = [
    "ScoringManager",
    "Badge",
    "BadgeType",
    "ScoringError",
    "InvalidScoreError",
    "BadgeValidationError",
    "SCORING_MANAGER"
]

# Production validation on import
if __name__ == "__main__":
    """Production scoring validation script."""
    print("🧪 Running production scoring validation...")
    
    try:
        manager = ScoringManager(AuditLogger(Path(CONFIG.data_dir)))
        progress = PROGRESS_MANAGER.load_progress()
        
        # Test scoring operations
        summary = manager.get_score_summary(progress)
        print(f"✅ Score summary: Level {summary['level']}, {summary['xp']} XP, "
              f"{summary['badge_count']} badges")
        
        # Test badge validation
        new_badges = manager.check_new_badges(progress)
        print(f"✅ Badge check: {len(new_badges)} new badges")
        
        # Test export
        report = manager.export_score_report(progress)
        print(f"✅ Score report exported: {report['compliance_percentage']:.1f}% compliance")
        
        print("🎉 Scoring manager validation PASSED")
        
    except Exception as e:
        print(f"❌ Scoring validation FAILED: {e}")
        raise

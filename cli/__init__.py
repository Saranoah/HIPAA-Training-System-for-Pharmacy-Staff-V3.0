#!/usr/bin/env python3
"""
CLI Package Initialization - HIPAA Training System v4.0.1
========================================================

Production-ready initialization for the CLI package:
- Clean exports for interface, commands, and display modules
- Modular command structure
- Zero-crash guarantee for CLI operations
- PythonAnywhere-optimized presentation layer
"""

from .interface import HIPAAComplianceCLI
from .display import DisplayManager
from .commands.lessons import LessonsCommand
from .commands.quiz import QuizCommand
from .commands.checklist import ChecklistCommand
from .commands.progress import ProgressCommand

__all__ = [
    "HIPAAComplianceCLI",
    "DisplayManager",
    "LessonsCommand",
    "QuizCommand",
    "ChecklistCommand",
    "ProgressCommand"
]

__version__ = "4.0.1"

# Production validation on import
if __name__ == "__main__":
    print("🧪 Validating CLI package initialization...")
    
    try:
        from core import CONFIG, PROGRESS_MANAGER
        
        # Initialize CLI components
        display = DisplayManager(CONFIG)
        cli = HIPAAComplianceCLI()
        
        # Test basic display functionality
        display.safe_print("✅ CLI package validation test", "green")
        
        print(f"✅ CLI package v{__version__} validated successfully")
        
    except Exception as e:
        print(f"❌ CLI package validation failed: {e}")
        raise

#!/usr/bin/env python3
"""
CLI Package Initialization - HIPAA Training System v4.0.1
========================================================

Production-ready initialization for the CLI package:
- Clean exports for CLI and supporting classes
- Zero-crash guarantee for CLI operations
- PythonAnywhere-optimized presentation layer
"""

from .cli import (
    HIPAAComplianceCLI,
    DisplayManager,
    LessonsCommand,
    QuizCommand,
    ChecklistCommand,
    ProgressCommand
)

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
        from core import CONFIG
        
        # Initialize CLI components
        display = DisplayManager(CONFIG)
        cli = HIPAAComplianceCLI()
        
        # Test basic display functionality
        display.safe_print("✅ CLI package validation test", "green")
        
        print(f"✅ CLI package v{__version__} validated successfully")
        
    except Exception as e:
        print(f"❌ CLI package validation failed: {e}")
        raise

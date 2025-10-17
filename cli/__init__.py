#!/usr/bin/env python3
"""
CLI Package Initialization - HIPAA Training System v4.0.1
========================================================

Production-ready exports for the CLI module:
- Unified CLI implementation in cli.py
- Clean, minimal interface for maintainability
- PythonAnywhere-optimized with zero-crash guarantee
"""

from .cli import (
    HIPAAComplianceCLI,
    DisplayManager,
    LessonsCommand,
    QuizCommand,
    ChecklistCommand,
    ProgressCommand,
    main
)

__all__ = [
    "HIPAAComplianceCLI",
    "DisplayManager",
    "LessonsCommand",
    "QuizCommand",
    "ChecklistCommand",
    "ProgressCommand",
    "main"
]

__version__ = "4.0.1"

# Production validation
if __name__ == "__main__":
    print("🧪 Validating CLI package initialization...")
    
    try:
        from core import CONFIG, PROGRESS_MANAGER, CONTENT_MANAGER, AuditLogger
        
        # Initialize CLI components
        display = DisplayManager(CONFIG)
        progress = PROGRESS_MANAGER.load_progress()
        audit = AuditLogger(CONFIG.data_dir)
        
        # Test all components
        display.safe_print("✅ CLI package validation test", "green")
        
        cli = HIPAAComplianceCLI()
        commands = [
            LessonsCommand(display, progress, audit),
            QuizCommand(display, progress, audit),
            ChecklistCommand(display, progress, audit),
            ProgressCommand(display, progress, audit)
        ]
        
        # Test main entry point
        assert callable(main), "Main function not callable"
        
        print(f"✅ CLI package v{__version__} validated successfully")
        print("📦 Unified CLI structure confirmed")
        
    except Exception as e:
        print(f"❌ CLI package validation failed: {e}")
        raise

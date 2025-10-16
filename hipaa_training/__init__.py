# hipaa_training/__init__.py
__version__ = "3.0.1"
__author__ = "Israa Ali"

from .cli import CLI
from .models import DatabaseManager, UserManager, ComplianceDashboard
from .security import SecurityManager
from .training_engine import EnhancedTrainingEngine
from .content_manager import ContentManager
from .compliance_dashboard import ComplianceDashboard

__all__ = [
    'CLI',
    'DatabaseManager',
    'UserManager',
    'ComplianceDashboard',
    'SecurityManager',
    'EnhancedTrainingEngine',
    'ContentManager'
]

# Module-level documentation
"""
HIPAA Training System
----------------------
This package provides a comprehensive solution for managing HIPAA training, including user management, content delivery, quiz assessments, and compliance checklists.

Classes:
- CLI: Command-line interface for interacting with the training system.
- DatabaseManager: Manages the database operations for user and training data.
- UserManager: Manages user creation, authentication, and management.
- ComplianceDashboard: Generates compliance reports and statistics.
- SecurityManager: Manages security features such as encryption, audit logging, and rate limiting.
- EnhancedTrainingEngine: Handles the user learning workflow, including lessons, quizzes, and final exams.
- ContentManager: Manages training content, including lessons, quizzes, and checklists.

Usage:
To use the package, import the desired classes and functions and call their methods as needed.
"""

# Example usage
if __name__ == "__main__":
    from .cli import CLI
    cli = CLI()
    cli.run()

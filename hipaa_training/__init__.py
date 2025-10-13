# hipaa_training/__init__.py
"""
HIPAA Training System V3.0.1
A production-ready training application for pharmacy staff
"""

__version__ = "3.0.1"
__author__ = "Israa Ali"

from .cli import CLI
from .models import DatabaseManager, UserManager, ComplianceDashboard
from .security import SecurityManager
from .training_engine import EnhancedTrainingEngine
from .content_manager import ContentManager

__all__ = [
    'CLI',
    'DatabaseManager',
    'UserManager',
    'ComplianceDashboard',
    'SecurityManager',
    'EnhancedTrainingEngine',
    'ContentManager'
]

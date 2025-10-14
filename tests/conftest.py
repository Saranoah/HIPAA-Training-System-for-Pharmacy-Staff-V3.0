# tests/conftest.py
"""
Pytest configuration and shared fixtures with real database support
"""
import pytest
import os
import sys
import shutil
from pathlib import Path
from unittest.mock import Mock

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables BEFORE any imports
os.environ['HIPAA_ENCRYPTION_KEY'] = 'test-key-for-testing-purposes-only-32-characters-long'
os.environ['HIPAA_SALT'] = 'test-salt-hex-16-bytes-long'


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment - runs once for entire test session"""
    # Create necessary directories
    test_dirs = ['data', 'content', 'reports', 'evidence', 'logs', 'certificates']
    for d in test_dirs:
        Path(d).mkdir(exist_ok=True)
    
    yield
    
    # Cleanup after all tests (except content)
    for d in test_dirs:
        if d != 'content' and Path(d).exists():
            shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="function")
def temp_db(tmp_path):
    """
    Provide a temporary database file for each test
    This ensures test isolation - each test gets a fresh database
    """
    db_file = tmp_path / "test_hipaa.db"
    
    # Save original DB_URL
    original_db_url = os.environ.get('DB_URL')
    
    # Set temporary database path
    os.environ['DB_URL'] = str(db_file)
    
    yield str(db_file)
    
    # Restore original DB_URL
    if original_db_url:
        os.environ['DB_URL'] = original_db_url
    else:
        os.environ.pop('DB_URL', None)
    
    # Database file is automatically cleaned up by tmp_path


@pytest.fixture
def real_user_manager(temp_db):
    """
    Provide a UserManager with a real temporary database
    Use this for integration tests
    """
    from hipaa_training.models import UserManager
    manager = UserManager()
    return manager


@pytest.fixture
def real_training_engine(temp_db):
    """
    Provide a TrainingEngine with real database
    Use this for integration tests
    """
    from hipaa_training.training_engine import EnhancedTrainingEngine
    engine = EnhancedTrainingEngine()
    return engine


@pytest.fixture
def real_compliance_dashboard(temp_db):
    """
    Provide a ComplianceDashboard with real database
    """
    from hipaa_training.models import ComplianceDashboard
    dashboard = ComplianceDashboard()
    return dashboard

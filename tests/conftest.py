# tests/conftest.py
"""
Pytest configuration and shared fixtures
"""
import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables before any imports
os.environ['HIPAA_ENCRYPTION_KEY'] = 'test-key-for-testing-purposes-only-32chars'
os.environ['HIPAA_SALT'] = 'test-salt-hex-16bytes'


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment - runs once for entire test session"""
    # Create temporary directories for tests
    test_dirs = ['data', 'content', 'reports', 'evidence', 'logs']
    for d in test_dirs:
        Path(d).mkdir(exist_ok=True)
    
    # Use in-memory database for tests
    os.environ['DB_URL'] = ':memory:'
    
    yield
    
    # Cleanup after all tests
    for d in test_dirs:
        if Path(d).exists():
            shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="function")
def temp_db(tmp_path):
    """Provide a temporary database file for tests that need persistent DB"""
    db_file = tmp_path / "test_hipaa.db"
    original_db_url = os.environ.get('DB_URL')
    
    # Set temporary database path
    os.environ['DB_URL'] = str(db_file)
    
    yield str(db_file)
    
    # Restore original
    if original_db_url:
        os.environ['DB_URL'] = original_db_url
    
    # Cleanup
    if db_file.exists():
        db_file.unlink()


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment for each test"""
    # This runs before each test
    yield
    # This runs after each test - cleanup if needed
    pass

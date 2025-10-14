# tests/conftest.py
"""
Pytest configuration and shared fixtures
"""
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables before any imports
os.environ['HIPAA_ENCRYPTION_KEY'] = 'test-key-for-testing-purposes-only-32chars'
os.environ['HIPAA_SALT'] = 'test-salt-hex-16bytes'
os.environ['DB_URL'] = ':memory:'  # Use in-memory database for tests


@pytest.fixture(scope="session")
def test_env():
    """Setup test environment"""
    # Create temporary directories
    test_dirs = ['test_content', 'test_reports', 'test_evidence']
    for d in test_dirs:
        Path(d).mkdir(exist_ok=True)

    yield

    # Cleanup
    import shutil
    for d in test_dirs:
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment for each test"""
    # This runs before each test
    yield
    # This runs after each test
    pass

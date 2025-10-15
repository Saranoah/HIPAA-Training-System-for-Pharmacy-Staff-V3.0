# tests/conftest.py
"""
Pytest configuration with real database support
"""
import pytest
import os
import sys
import shutil
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variables BEFORE imports
os.environ['HIPAA_ENCRYPTION_KEY'] = 'test-key-32-chars-long-enough-for-testing'
os.environ['HIPAA_SALT'] = 'test-salt-16-hex-bytes'


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup directories for all tests"""
    dirs = ['data', 'content', 'reports', 'evidence', 'logs', 'certificates']
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    yield
    for d in dirs:
        if d != 'content' and Path(d).exists():
            shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="function")
def temp_db(tmp_path):
    """Provide temporary database for each test"""
    db_file = tmp_path / "test.db"
    original = os.environ.get('DB_URL')
    os.environ['DB_URL'] = str(db_file)
    yield str(db_file)
    if original:
        os.environ['DB_URL'] = original
    else:
        os.environ.pop('DB_URL', None)


@pytest.fixture
def training_engine(temp_db):
    """Real training engine with temp database"""
    from hipaa_training.training_engine import EnhancedTrainingEngine
    from unittest.mock import Mock
    engine = EnhancedTrainingEngine()
    engine.console = Mock()  # Mock console to suppress output
    return engine

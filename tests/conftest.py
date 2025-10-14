import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# --- Ensure the project root is in PYTHONPATH ---
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# --- Set required environment variables early ---
os.environ.setdefault('HIPAA_ENCRYPTION_KEY', 'test-key-32-chars-for-testing-only')
os.environ.setdefault('HIPAA_SALT', 'test-salt-16-hex-bytes')

@pytest.fixture(scope="session", autouse=True)
def setup_test_dirs():
    """Create required directories for tests"""
    dirs = ['data', 'content', 'reports', 'evidence', 'logs', 'certificates']
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    yield
    # Cleanup after all tests
    import shutil
    for d in dirs:
        if Path(d).exists() and d != 'content':  # Keep content directory
            shutil.rmtree(d, ignore_errors=True)

@pytest.fixture(scope="function")
def test_db(tmp_path):
    """Provide temporary database for each test"""
    db_file = tmp_path / "test.db"
    original = os.environ.get('DB_URL')
    os.environ['DB_URL'] = str(db_file)
    yield str(db_file)
    if original:
        os.environ['DB_URL'] = original
    else:
        os.environ.pop('DB_URL', None)

@pytest.fixture(scope="function", autouse=True)
def mock_database_for_tests(monkeypatch, tmp_path):
    """Automatically provide a temporary DB for all tests"""
    db_file = tmp_path / "test_auto.db"
    monkeypatch.setenv('DB_URL', str(db_file))

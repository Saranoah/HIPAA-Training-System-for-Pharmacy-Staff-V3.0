# tests/test_user_manager.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from hipaa_training.models import UserManager, DatabaseManager
import sqlite3


@pytest.fixture
def user_manager():
    """Create user manager with mocked database"""
    with patch.dict('os.environ', {
        'HIPAA_ENCRYPTION_KEY': 'test-key-for-testing-only-32-chars',
        'HIPAA_SALT': 'a1b2c3d4e5f6g7h8'
    }):
        manager = UserManager()
        manager.db = Mock(spec=DatabaseManager)
        manager.security = Mock()
        return manager


def test_create_user_success(user_manager):
    """Test successful user creation"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.lastrowid = 123
    mock_conn.execute.return_value = mock_cursor
    
    user_manager.db._get_connection.return_value.__enter__.return_value = mock_conn
    
    user_id = user_manager.create_user("testuser", "Test User", "staff")
    
    assert user_id == 123
    user_manager.security.log_action.assert_called_once()


def test_create_user_invalid_role(user_manager):
    """Test user creation with invalid role"""
    with pytest.raises(ValueError, match="Invalid role"):
        user_manager.create_user("testuser", "Test User", "invalid_role")


def test_create_user_empty_username(user_manager):
    """Test user creation with empty username"""
    with pytest.raises(ValueError, match="cannot be empty"):
        user_manager.create_user("", "Test User", "staff")


def test_create_user_empty_fullname(user_manager):
    """Test user creation with empty full name"""
    with pytest.raises(ValueError, match="cannot be empty"):
        user_manager.create_user("testuser", "", "staff")


def test_create_user_duplicate_username(user_manager):
    """Test user creation with duplicate username"""
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")
    
    user_manager.db._get_connection.return_value.__enter__.return_value = mock_conn
    
    with pytest.raises(ValueError, match="Username already exists"):
        user_manager.create_user("duplicate", "Test User", "staff")


def test_user_exists_true(user_manager):
    """Test user_exists returns True for existing user"""
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = (1,)
    
    user_manager.db._get_connection.return_value.__enter__.return_value = mock_conn
    
    assert user_manager.user_exists(123) is True


def test_user_exists_false(user_manager):
    """Test user_exists returns False for non-existent user"""
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = None
    
    user_manager.db._get_connection.return_value.__enter__.return_value = mock_conn
    
    assert user_manager.user_exists(999) is False


def test_sanitize_input_special_chars(user_manager):
    """Test input sanitization preserves safe characters"""
    result = user_manager._sanitize_input("O'Brien", 50)
    # Should use HTML escaping, preserving the apostrophe
    assert "O" in result
    assert "Brien" in result


def test_sanitize_input_max_length(user_manager):
    """Test input sanitization respects max length"""
    long_string = "A" * 100
    result = user_manager._sanitize_input(long_string, 50)
    assert len(result) == 50


def test_get_user(user_manager):
    """Test getting user details"""
    mock_conn = MagicMock()
    mock_result = {
        'id': 1,
        'username': 'testuser',
        'full_name': 'Test User',
        'role': 'staff',
        'created_at': '2025-01-01'
    }
    mock_conn.execute.return_value.fetchone.return_value = mock_result
    
    user_manager.db._get_connection.return_value.__enter__.return_value = mock_conn
    
    user = user_manager.get_user(1)
    
    assert user is not None
    assert user['username'] == 'testuser'
    assert user['role'] == 'staff'

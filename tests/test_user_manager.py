# tests/test_user_manager.py
"""Tests for UserManager with real database"""
import pytest
from hipaa_training.models import UserManager


@pytest.fixture
def user_manager(temp_db):
    """Real UserManager with temp database"""
    return UserManager()


def test_create_user_success(user_manager):
    """Test successful user creation"""
    user_id = user_manager.create_user("testuser", "Test User", "staff")
    assert user_id > 0
    assert user_manager.user_exists(user_id)


def test_create_user_invalid_role(user_manager):
    """Test invalid role"""
    with pytest.raises(ValueError, match="Invalid role"):
        user_manager.create_user("user", "Name", "bad_role")


def test_create_user_empty_username(user_manager):
    """Test empty username"""
    with pytest.raises(ValueError, match="cannot be empty"):
        user_manager.create_user("", "Name", "staff")


def test_create_user_empty_fullname(user_manager):
    """Test empty full name"""
    with pytest.raises(ValueError, match="cannot be empty"):
        user_manager.create_user("user", "", "staff")


def test_create_user_duplicate_username(user_manager):
    """Test duplicate username"""
    user_manager.create_user("dup", "User 1", "staff")
    with pytest.raises(ValueError, match="already exists"):
        user_manager.create_user("dup", "User 2", "staff")


def test_user_exists_true(user_manager):
    """Test user exists"""
    user_id = user_manager.create_user("exists", "Name", "staff")
    assert user_manager.user_exists(user_id) is True


def test_user_exists_false(user_manager):
    """Test user doesn't exist"""
    assert user_manager.user_exists(99999) is False


def test_sanitize_input_special_chars(user_manager):
    """Test sanitization preserves characters"""
    result = user_manager._sanitize_input("O'Brien", 50)
    assert "O" in result and "Brien" in result


def test_sanitize_input_max_length(user_manager):
    """Test max length enforcement"""
    result = user_manager._sanitize_input("A" * 100, 50)
    assert len(result) == 50


def test_get_user(user_manager):
    """Test getting user details"""
    user_id = user_manager.create_user("getuser", "Get User", "staff")
    user = user_manager.get_user(user_id)
    assert user is not None
    assert user['username'] == "getuser"

import pytest
from hipaa_training.models import UserManager


@pytest.fixture
def user_manager(temp_db):
    """Provide real database-backed UserManager"""
    return UserManager()


def test_create_user_success(user_manager):
    """Create user successfully"""
    uid = user_manager.create_user("alice", "Alice Example", "staff")
    assert uid > 0
    assert user_manager.user_exists(uid)


def test_create_user_duplicate_username(user_manager):
    """Duplicate username should raise ValueError"""
    user_manager.create_user("duplicate", "First", "staff")
    with pytest.raises(ValueError, match="Username already exists"):
        user_manager.create_user("duplicate", "Second", "staff")


def test_user_exists_true(user_manager):
    """Existing user should return True"""
    uid = user_manager.create_user("exists", "Name", "admin")
    assert user_manager.user_exists(uid)


def test_user_exists_false(user_manager):
    """Nonexistent user should return False"""
    assert not user_manager.user_exists(999999)


def test_get_user(user_manager):
    """Retrieve user info"""
    uid = user_manager.create_user("bob", "Bob Example", "staff")
    user = user_manager.get_user(uid)
    assert user["username"] == "bob"
    assert user["role"] == "staff"

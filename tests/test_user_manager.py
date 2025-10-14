# tests/test_user_manager.py
import sqlite3
import pytest
from unittest.mock import patch

def test_create_user_success(real_user_manager):
    """Create a user and verify existence in DB."""
    um = real_user_manager
    user_id = um.create_user("alice", "Alice Example", "staff")
    assert isinstance(user_id, int) and user_id > 0
    assert um.user_exists(user_id)

def test_create_user_invalid_role(real_user_manager):
    with pytest.raises(ValueError, match="Invalid role"):
        real_user_manager.create_user("bob", "Bob Example", "invalid_role")

def test_create_user_empty_username_or_fullname(real_user_manager):
    with pytest.raises(ValueError):
        real_user_manager.create_user("", "Name", "staff")
    with pytest.raises(ValueError):
        real_user_manager.create_user("uname", "", "staff")

def test_create_user_duplicate_username(real_user_manager):
    um = real_user_manager
    uid1 = um.create_user("dupuser", "First", "staff")
    assert uid1 > 0
    with pytest.raises(ValueError, match="Username already exists"):
        um.create_user("dupuser", "Second", "staff")

def test_user_exists_true_false(real_user_manager):
    um = real_user_manager
    uid = um.create_user("exists_user", "Exists", "staff")
    assert um.user_exists(uid) is True
    assert um.user_exists(999999) is False

def test_sanitize_input_special_chars_and_max_length(real_user_manager):
    um = real_user_manager
    long_name = "A" * 200
    uid = um.create_user("user!<>", long_name, "staff")
    user = um.get_user(uid)
    # username should be sanitized (HTML-escaped) and truncated
    assert "user" in user["username"]
    assert len(user["full_name"]) <= 100

def test_get_user_returns_none_for_missing(real_user_manager):
    assert real_user_manager.get_user(999999) is None

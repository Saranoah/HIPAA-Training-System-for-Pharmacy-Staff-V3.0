#!/usr/bin/env python3
#scripts/manual_test.py
"""
Interactive manual testing script
Guides tester through complete user workflow
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hipaa_training.models import UserManager, DatabaseManager, ComplianceDashboard
from hipaa_training.security import SecurityManager
from hipaa_training.training_engine import EnhancedTrainingEngine


def test_user_creation():
    """Test user creation"""
    print("\n" + "="*60)
    print("TEST 1: User Creation")
    print("="*60)

    try:
        manager = UserManager()

        # Create test user
        user_id = manager.create_user("test_user", "Test User", "staff")
        print(f"✓ User created with ID: {user_id}")

        # Verify user exists
        if manager.user_exists(user_id):
            print(f"✓ User verification passed")
        else:
            print(f"✗ User verification failed")
            return False

        # Get user details
        user = manager.get_user(user_id)
        print(f"✓ User details retrieved: {user['username']}")

        return True

    except Exception as e:
        print(f"✗ User creation failed: {e}")
        return False


def test_content_loading():
    """Test content manager"""
    print("\n" + "="*60)
    print("TEST 2: Content Loading")
    print("="*60)

    try:
        from hipaa_training.content_manager import ContentManager

        cm = ContentManager()

        # Check lessons
        lesson_count = len(cm.lessons)
        print(f"✓ Loaded {lesson_count} lessons")

        # Check quiz questions
        quiz_count = len(cm.quiz_questions)
        print(f"✓ Loaded {quiz_count} quiz questions")

        # Check checklist
        checklist_count = len(cm.checklist_items)
        print(f"✓ Loaded {checklist_count} checklist items")

        if lesson_count >= 3 and quiz_count >= 5 and checklist_count >= 10:
            print("✓ Content validation passed")
            return True
        else:
            print("✗ Insufficient content")
            return False

    except Exception as e:
        print(f"✗ Content loading failed: {e}")
        return False


def test_encryption():
    """Test encryption/decryption"""
    print("\n" + "="*60)
    print("TEST 3: Encryption/Decryption")
    print("="*60)

    try:
        security = SecurityManager()

        test_data = "Sensitive PHI Data: Patient John Doe, DOB: 1980-01-01"

        # Encrypt
        encrypted = security.encrypt_data(test_data)
        print(f"✓ Data encrypted (length: {len(encrypted)})")

        # Decrypt
        decrypted = security.decrypt_data(encrypted)
        print(f"✓ Data decrypted")

        # Verify
        if decrypted == test_data:
            print("✓ Encryption verification passed")
            return True
        else:
            print("✗ Decrypted data doesn't match original")
            return False

    except Exception as e:
        print(f"✗ Encryption test failed: {e}")
        return False


def test_database_operations():
    """Test database operations"""
    print("\n" + "="*60)
    print("TEST 4: Database Operations")
    print("="*60)

    try:
        db = DatabaseManager()
        manager = UserManager()

        # Create test user
        user_id = manager.create_user("db_test_user", "DB Test User", "staff")
        print(f"✓ Test user created: {user_id}")

        # Save progress
        db.save_progress(user_id, "Test Lesson", 85.0, None)
        print("✓ Progress saved")

        # Issue certificate
        cert_id = db.issue_certificate(user_id, 85.0)
        print(f"✓ Certificate issued: {cert_id}")

        # Get statistics
        stats = db.get_compliance_stats()
        print(f"✓ Statistics retrieved: {stats['total_users']} users")

        return True

    except Exception as e:
        print(f"✗ Database operations failed: {e}")
        return False


def test_report_generation():
    """Test report generation"""
    print("\n" + "="*60)
    print("TEST 5: Report Generation")
    print("="*60)

    try:
        dashboard = ComplianceDashboard()

        # Generate CSV
        csv_file_file

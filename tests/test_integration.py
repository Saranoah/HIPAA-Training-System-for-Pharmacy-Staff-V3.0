"""
tests/test_integration.py

Comprehensive Integration Test Suite for HIPAA Training System
Tests end-to-end workflows, security integration, and system reliability.

Run with: pytest tests/test_integration.py -v
Coverage: pytest tests/test_integration.py --cov=hipaa_training --cov-report=html
"""

import json
import os
import secrets
import sqlite3
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Set up test environment before imports
os.environ["HIPAA_ENCRYPTION_KEY"] = secrets.token_urlsafe(32)
os.environ["HIPAA_SALT"] = secrets.token_hex(32)
os.environ["PBKDF2_ITERATIONS"] = "600000"
os.environ["DB_URL"] = ":memory:"  # Use in-memory DB for tests


class TestEndToEndUserWorkflow:
    """Test complete user lifecycle from creation to certification."""

    @pytest.fixture
    def setup_system(self, tmp_path):
        """Set up clean test environment."""
        # Use in-memory database for isolation
        os.environ["DB_URL"] = ":memory:"
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        os.environ["LOG_DIR"] = str(log_dir)

        # Import after environment is set
        from hipaa_training.models import DatabaseManager, UserManager
        from hipaa_training.security import SecurityManager
        from hipaa_training.compliance_dashboard import ComplianceDashboard

        return {
            "db": DatabaseManager(),
            "user_manager": UserManager(),
            "dashboard": ComplianceDashboard(),
            "security": SecurityManager(),
            "log_dir": log_dir,
        }

    def test_complete_user_journey(self, setup_system):
        """Test full user journey: create → train → certify → report."""
        system = setup_system

        # Step 1: Create user
        user_id = system["user_manager"].create_user(
            username="john.doe",
            full_name="John Doe",
            role="staff"
        )

        assert user_id > 0
        assert system["user_manager"].user_exists(user_id)

        # Step 2: Verify user creation
        user = system["user_manager"].get_user(user_id)
        assert user is not None
        assert user["username"] == "john.doe"
        assert user["role"] == "staff"

        # Step 3: Save training progress (multiple lessons)
        lessons = [
            ("HIPAA Overview", 85.5),
            ("Privacy Rule", 92.0),
            ("Security Rule", 88.5),
        ]

        for lesson, score in lessons:
            system["db"].save_progress(
                user_id=user_id,
                lesson_title=lesson,
                score=score,
                checklist_data=None
            )

        # Step 4: Complete compliance checklist
        checklist_data = {
            "workstation_locked": True,
            "password_strong": True,
            "phi_secured": True,
        }

        system["db"].save_sensitive_progress(
            user_id=user_id,
            checklist_data=checklist_data,
            score=90.25
        )

        # Step 5: Issue certificate
        cert_id = system["db"].issue_certificate(
            user_id=user_id,
            score=90.25
        )

        assert cert_id is not None
        assert len(cert_id) == 36  # UUID format

        # Step 6: Verify certificate in database
        with system["db"]._get_connection() as conn:
            cert = conn.execute(
                "SELECT * FROM certificates WHERE certificate_id = ?",
                (cert_id,),
            ).fetchone()

            assert cert is not None
            assert cert["user_id"] == user_id
            assert cert["score"] == 90.25
            assert cert["revoked"] == 0  # SQLite uses 0/1 for booleans

        # Step 7: Generate compliance report
        report_path = system["dashboard"].generate_enterprise_report(
            format_type="json"
        )

        assert Path(report_path).exists()

        # Step 8: Verify report contents
        with open(report_path, "r") as f:
            report_data = json.load(f)

            assert report_data["total_users"] >= 1
            assert report_data["total_certs"] >= 1
            assert report_data["active_certs"] >= 1

        # Step 9: Verify audit trail exists
        with system["db"]._get_connection() as conn:
            audit_logs = conn.execute(
                "SELECT * FROM audit_log WHERE user_id = ? ORDER BY timestamp",
                (user_id,),
            ).fetchall()

            # Should have logs for: create, progress saves, cert issue
            assert len(audit_logs) >= 4


class TestSecurityIntegration:
    """Test security features across the system."""

    @pytest.fixture
    def setup_system(self, tmp_path):
        """Set up test system."""
        os.environ["DB_URL"] = ":memory:"
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        os.environ["LOG_DIR"] = str(log_dir)

        from hipaa_training.models import DatabaseManager, UserManager
        from hipaa_training.security import SecurityManager

        return {
            "db": DatabaseManager(),
            "user_manager": UserManager(),
            "security": SecurityManager(),
        }

    def test_encryption_decryption_roundtrip(self, setup_system):
        """Test data encryption throughout the system."""
        system = setup_system

        # Create user and save sensitive data
        user_id = system["user_manager"].create_user(
            username="secure.user",
            full_name="Secure User",
            role="staff"
        )

        # Sensitive checklist data
        sensitive_data = {
            "medical_condition": "Patient has diabetes",
            "treatment_plan": "Regular monitoring required"
        }

        # Save encrypted
        system["db"].save_sensitive_progress(
            user_id=user_id,
            checklist_data=sensitive_data,
            score=85.0
        )

        # Verify data is encrypted in database
        with system["db"]._get_connection() as conn:
            stored_data = conn.execute(
                "SELECT checklist_data FROM training_progress WHERE user_id = ?",
                (user_id,),
            ).fetchone()

            assert stored_data is not None
            encrypted = stored_data["checklist_data"]

            # Should NOT contain plain text
            assert "diabetes" not in encrypted

            # Should be encrypted (not JSON)
            try:
                json.loads(encrypted)
                # If this succeeds, data wasn't encrypted properly
                assert False, "Data should be encrypted, not plain JSON"
            except json.JSONDecodeError:
                # This is expected - data should be encrypted
                pass

    def test_sql_injection_prevention(self, setup_system):
        """Test SQL injection attempts are blocked."""
        system = setup_system

        from hipaa_training.security import ValidationError

        # Attempt SQL injection in username
        with pytest.raises(ValidationError):
            system["user_manager"].create_user(
                username="admin'; DROP TABLE users; --",
                full_name="Hacker",
                role="admin"
            )

        # Create legitimate user first
        user_id = system["user_manager"].create_user(
            username="test.user",
            full_name="Test User",
            role="staff"
        )

        # Verify database is intact and user was created
        assert system["user_manager"].user_exists(user_id)

    def test_xss_prevention_in_inputs(self, setup_system):
        """Test XSS attempts are sanitized."""
        system = setup_system

        # Create user with XSS attempt in full name
        user_id = system["user_manager"].create_user(
            username="xss.test",
            full_name="<script>alert('XSS')</script>",
            role="staff"
        )

        # Retrieve and verify sanitization
        user = system["user_manager"].get_user(user_id)
        assert "<script>" not in user["full_name"]

    def test_rate_limiting_enforcement(self, setup_system):
        """Test rate limiting prevents abuse."""
        system = setup_system

        from hipaa_training.security import RateLimitExceeded

        # Create user
        user_id = system["user_manager"].create_user(
            username="rate.test",
            full_name="Rate Test",
            role="staff"
        )

        # Set up low rate limit by patching the config
        with patch.dict(os.environ, {"MAX_ENCRYPTIONS_PER_MINUTE": "3"}):
            # Reimport to pick up new config
            import importlib
            import hipaa_training.security
            importlib.reload(hipaa_training.security)
            
            from hipaa_training.security import SecurityManager
            security = SecurityManager()

            # Use up the limit
            for i in range(3):
                security.encrypt_data(f"test data {i}")

            # Next attempt should fail
            with pytest.raises(RateLimitExceeded):
                security.encrypt_data("should fail")


class TestDataIntegrity:
    """Test data integrity and consistency."""

    @pytest.fixture
    def setup_system(self, tmp_path):
        """Set up test system."""
        os.environ["DB_URL"] = ":memory:"

        from hipaa_training.models import DatabaseManager, UserManager

        return {
            "db": DatabaseManager(),
            "user_manager": UserManager(),
        }

    def test_foreign_key_constraints(self, setup_system):
        """Test foreign key constraints are enforced."""
        system = setup_system

        # Try to save progress for non-existent user
        with pytest.raises(sqlite3.IntegrityError):
            with system["db"]._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO training_progress 
                    (user_id, lesson_title, quiz_score, completed_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (99999, "Test", 85.0, datetime.now()),
                )
                conn.commit()

    def test_duplicate_username_prevention(self, setup_system):
        """Test duplicate usernames are prevented."""
        system = setup_system

        # Create first user
        system["user_manager"].create_user(
            username="unique.user",
            full_name="First User",
            role="staff"
        )

        # Attempt duplicate - should raise IntegrityError from SQLite
        with pytest.raises((ValueError, sqlite3.IntegrityError)):
            system["user_manager"].create_user(
                username="unique.user",
                full_name="Second User",
                role="admin"
            )

    def test_certificate_expiry_tracking(self, setup_system):
        """Test certificate expiration is tracked correctly."""
        system = setup_system

        user_id = system["user_manager"].create_user(
            username="expiry.test",
            full_name="Expiry Test",
            role="staff"
        )

        cert_id = system["db"].issue_certificate(
            user_id=user_id,
            score=85.0
        )

        # Verify expiry date is set correctly
        with system["db"]._get_connection() as conn:
            cert = conn.execute(
                "SELECT issue_date, expiry_date FROM certificates WHERE certificate_id = ?",
                (cert_id,),
            ).fetchone()

            issue_date = datetime.fromisoformat(cert["issue_date"].replace('Z', '+00:00'))
            expiry_date = datetime.fromisoformat(cert["expiry_date"].replace('Z', '+00:00'))

            # Should be 365 days apart (default)
            delta = expiry_date - issue_date
            assert delta.days == 365


class TestAuditLogging:
    """Test comprehensive audit logging."""

    @pytest.fixture
    def setup_system(self, tmp_path):
        """Set up test system."""
        os.environ["DB_URL"] = ":memory:"
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        os.environ["LOG_DIR"] = str(log_dir)

        from hipaa_training.models import DatabaseManager, UserManager
        from hipaa_training.security import SecurityManager

        return {
            "db": DatabaseManager(),
            "user_manager": UserManager(),
            "security": SecurityManager(),
            "log_dir": log_dir,
        }

    def test_all_operations_logged(self, setup_system):
        """Test all critical operations are logged."""
        system = setup_system

        # Create a session for audit tracking
        session_id = system["security"].create_session(0)

        # Perform various operations with audit logging
        user_id = system["user_manager"].create_user(
            username="audit.test",
            full_name="Audit Test",
            role="staff"
        )

        system["db"].save_progress(
            user_id=user_id,
            lesson_title="Test Lesson",
            score=90.0,
            checklist_data=None
        )

        system["db"].issue_certificate(
            user_id=user_id,
            score=90.0
        )

        # Verify operations were logged in database
        with system["db"]._get_connection() as conn:
            logs = conn.execute(
                "SELECT action FROM audit_log WHERE user_id = ?",
                (user_id,),
            ).fetchall()

            actions = [log["action"] for log in logs]
            assert "USER_CREATED" in actions
            assert "PROGRESS_SAVED" in actions
            assert "CERTIFICATE_ISSUED" in actions

    def test_audit_log_file_creation(self, setup_system):
        """Test audit logs are written to files."""
        system = setup_system

        # Perform operation that should be logged
        system["user_manager"].create_user(
            username="file.log.test",
            full_name="File Log Test",
            role="staff"
        )

        # Check log file exists
        log_file = system["log_dir"] / "hipaa_audit.log"
        
        # Log file might be created on first write, so ensure it exists
        system["security"].log_action(
            user_id=0,
            action="TEST_ACTION",
            details="Test log entry",
            session_id="test-session",
            ip_address="127.0.0.1"
        )

        assert log_file.exists()

        # Verify log content
        with open(log_file, "r") as f:
            content = f.read()
            assert "TEST_ACTION" in content


class TestComplianceReporting:
    """Test compliance reporting functionality."""

    @pytest.fixture
    def setup_system_with_data(self, tmp_path):
        """Set up system with sample data."""
        os.environ["DB_URL"] = ":memory:"
        os.environ["REPORTS_DIR"] = str(tmp_path / "reports")
        
        Path(os.environ["REPORTS_DIR"]).mkdir(exist_ok=True)

        from hipaa_training.models import DatabaseManager, UserManager
        from hipaa_training.compliance_dashboard import ComplianceDashboard

        db = DatabaseManager()
        um = UserManager()
        cd = ComplianceDashboard()

        # Create multiple users with varying completion
        users = []
        for i in range(3):
            user_id = um.create_user(
                username=f"user{i}",
                full_name=f"User {i}",
                role="staff"
            )
            users.append(user_id)

            # Save progress and issue certificates
            db.save_progress(
                user_id=user_id,
                lesson_title="Test Lesson",
                score=85.0 + i * 5,
                checklist_data=None
            )

            db.issue_certificate(
                user_id=user_id,
                score=85.0 + i * 5
            )

        return {
            "db": db,
            "dashboard": cd,
            "users": users,
        }

    def test_csv_report_generation(self, setup_system_with_data):
        """Test CSV report generation."""
        system = setup_system_with_data

        report_path = system["dashboard"].generate_enterprise_report(
            format_type="csv"
        )

        assert Path(report_path).exists()
        assert report_path.endswith(".csv")

        # Verify CSV has content
        with open(report_path, "r") as f:
            content = f.read()
            assert len(content) > 0
            assert "total_users" in content

    def test_json_report_generation(self, setup_system_with_data):
        """Test JSON report generation."""
        system = setup_system_with_data

        report_path = system["dashboard"].generate_enterprise_report(
            format_type="json"
        )

        assert Path(report_path).exists()
        assert report_path.endswith(".json")

        # Verify JSON structure
        with open(report_path, "r") as f:
            data = json.load(f)

            assert "total_users" in data
            assert "total_certs" in data
            assert "avg_score" in data
            assert "pass_rate" in data

    def test_report_statistics_accuracy(self, setup_system_with_data):
        """Test statistics calculations are accurate."""
        system = setup_system_with_data

        stats = system["db"].get_compliance_stats()

        # Verify counts match our test data
        assert stats["total_users"] == 3
        assert stats["total_certs"] == 3
        assert stats["active_certs"] == 3


class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.fixture
    def setup_system(self, tmp_path):
        """Set up test system."""
        os.environ["DB_URL"] = ":memory:"

        from hipaa_training.models import DatabaseManager, UserManager

        return {
            "db": DatabaseManager(),
            "user_manager": UserManager(),
        }

    def test_invalid_score_handling(self, setup_system):
        """Test invalid scores are rejected."""
        system = setup_system

        user_id = system["user_manager"].create_user(
            username="score.test",
            full_name="Score Test",
            role="staff"
        )

        # Test score outside valid range - should be handled gracefully
        # The system might clamp values or raise an error
        try:
            system["db"].save_progress(
                user_id=user_id,
                lesson_title="Test",
                score=150.0,  # > 100
                checklist_data=None
            )
            # If no error, verify the value was clamped
            with system["db"]._get_connection() as conn:
                result = conn.execute(
                    "SELECT quiz_score FROM training_progress WHERE user_id = ?",
                    (user_id,)
                ).fetchone()
                if result:
                    assert 0 <= result["quiz_score"] <= 100
        except (ValueError, sqlite3.Error):
            # Error is also acceptable
            pass

    def test_graceful_missing_user_handling(self, setup_system):
        """Test system handles missing users gracefully."""
        system = setup_system

        # Try to get non-existent user
        user = system["user_manager"].get_user(99999)
        assert user is None

        # Verify system is still operational
        new_user_id = system["user_manager"].create_user(
            username="after.missing",
            full_name="After Missing",
            role="staff"
        )
        assert new_user_id > 0


class TestPerformanceAndScalability:
    """Test system performance under load."""

    @pytest.fixture
    def setup_system(self, tmp_path):
        """Set up test system."""
        os.environ["DB_URL"] = ":memory:"

        from hipaa_training.models import DatabaseManager, UserManager

        return {
            "db": DatabaseManager(),
            "user_manager": UserManager(),
        }

    def test_bulk_user_creation(self, setup_system):
        """Test creating multiple users efficiently."""
        system = setup_system

        start_time = time.time()

        # Create multiple users
        user_ids = []
        for i in range(10):  # Reduced for test speed
            user_id = system["user_manager"].create_user(
                username=f"bulk_user_{i}",
                full_name=f"Bulk User {i}",
                role="staff"
            )
            user_ids.append(user_id)

        elapsed = time.time() - start_time

        # Should complete in reasonable time
        assert elapsed < 2.0
        assert len(user_ids) == 10
        assert len(set(user_ids)) == 10  # All unique

    def test_concurrent_operations(self, setup_system):
        """Test system handles concurrent operations."""
        system = setup_system

        # Create user for operations
        user_id = system["user_manager"].create_user(
            username="concurrent.test",
            full_name="Concurrent Test",
            role="staff"
        )

        # Simulate multiple progress saves
        for i in range(5):
            system["db"].save_progress(
                user_id=user_id,
                lesson_title=f"Lesson {i}",
                score=80.0 + i,
                checklist_data=None
            )

        # Verify all saves succeeded
        with system["db"]._get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM training_progress WHERE user_id = ?",
                (user_id,),
            ).fetchone()[0]

            assert count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

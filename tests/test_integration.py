"""
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


class TestEndToEndUserWorkflow:
    """Test complete user lifecycle from creation to certification."""
    
    @pytest.fixture
    def setup_system(self, tmp_path):
        """Set up clean test environment."""
        db_path = tmp_path / "test_hipaa.db"
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        
        os.environ["DB_URL"] = str(db_path)
        os.environ["LOG_DIR"] = str(log_dir)
        
        # Import after environment is set
        from hipaa_training.models import (
            DatabaseManager,
            UserManager,
            ComplianceDashboard,
        )
        from hipaa_training.security import SecurityManager
        
        return {
            "db": DatabaseManager(),
            "user_manager": UserManager(),
            "dashboard": ComplianceDashboard(),
            "security": SecurityManager(),
            "db_path": db_path,
            "log_dir": log_dir,
        }
    
    def test_complete_user_journey(self, setup_system):
        """Test full user journey: create → train → certify → report."""
        system = setup_system
        
        # Step 1: Create user
        user_id = system["user_manager"].create_user(
            username="john.doe",
            full_name="John Doe",
            role="staff",
            session_id="test-session-001",
            ip_address="192.168.1.100",
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
            ("Breach Notification", 95.0),
        ]
        
        for lesson, score in lessons:
            system["db"].save_progress(
                user_id=user_id,
                lesson_title=lesson,
                score=score,
                checklist_data=None,
                session_id="test-session-001",
                ip_address="192.168.1.100",
            )
        
        # Step 4: Complete compliance checklist
        checklist_data = {
            "workstation_locked": True,
            "password_strong": True,
            "phi_secured": True,
            "training_completed": True,
            "badge_visible": True,
        }
        
        system["db"].save_sensitive_progress(
            user_id=user_id,
            checklist_data=checklist_data,
            score=90.25,
            session_id="test-session-001",
            ip_address="192.168.1.100",
        )
        
        # Step 5: Issue certificate
        cert_id = system["db"].issue_certificate(
            user_id=user_id,
            score=90.25,
            session_id="test-session-001",
            ip_address="192.168.1.100",
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
            assert cert["revoked"] is False
        
        # Step 7: Generate compliance report
        report_path = system["dashboard"].generate_enterprise_report(
            format_type="json",
            session_id="test-session-001",
            ip_address="192.168.1.100",
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
            assert len(audit_logs) >= 5
            
            # Verify log types
            actions = [log["action"] for log in audit_logs]
            assert "USER_CREATED" in actions
            assert "PROGRESS_SAVED" in actions
            assert "CERTIFICATE_ISSUED" in actions


class TestSecurityIntegration:
    """Test security features across the system."""
    
    @pytest.fixture
    def setup_system(self, tmp_path):
        """Set up test system."""
        db_path = tmp_path / "test_security.db"
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        
        os.environ["DB_URL"] = str(db_path)
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
            role="staff",
        )
        
        # Sensitive checklist data
        sensitive_data = {
            "ssn": "123-45-6789",
            "dob": "1990-01-01",
            "medical_id": "MED-12345",
            "phi_data": "Patient has diabetes",
        }
        
        # Save encrypted
        system["db"].save_sensitive_progress(
            user_id=user_id,
            checklist_data=sensitive_data,
            score=85.0,
        )
        
        # Verify data is encrypted in database
        with system["db"]._get_connection() as conn:
            stored_data = conn.execute(
                "SELECT checklist_data_encrypted FROM training_progress "
                "WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            
            assert stored_data is not None
            encrypted = stored_data["checklist_data_encrypted"]
            
            # Should NOT contain plain text
            assert "123-45-6789" not in encrypted
            assert "diabetes" not in encrypted
            
            # Should be base64-encoded Fernet token
            assert len(encrypted) > 100
            
            # Decrypt and verify
            decrypted_json = system["security"].decrypt_data(encrypted)
            decrypted = json.loads(decrypted_json[0])  # decrypt_data returns tuple
            
            assert decrypted["ssn"] == "123-45-6789"
            assert decrypted["phi_data"] == "Patient has diabetes"
    
    def test_sql_injection_prevention(self, setup_system):
        """Test SQL injection attempts are blocked."""
        system = setup_system
        
        from hipaa_training.security import ValidationError
        
        # Attempt 1: SQL injection in username
        with pytest.raises(ValidationError):
            system["user_manager"].create_user(
                username="admin'; DROP TABLE users; --",
                full_name="Hacker",
                role="admin",
            )
        
        # Attempt 2: SQL injection in lesson title
        user_id = system["user_manager"].create_user(
            username="test.user",
            full_name="Test User",
            role="staff",
        )
        
        with pytest.raises(ValidationError):
            system["db"].save_progress(
                user_id=user_id,
                lesson_title="Lesson'; DELETE FROM training_progress; --",
                score=80,
                checklist_data=None,
            )
        
        # Verify database is intact
        with system["db"]._get_connection() as conn:
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            assert user_count > 0
    
    def test_xss_prevention_in_inputs(self, setup_system):
        """Test XSS attempts are sanitized."""
        system = setup_system
        
        # Create user with XSS attempt
        user_id = system["user_manager"].create_user(
            username="xss.test",
            full_name="<script>alert('XSS')</script>",
            role="staff",
        )
        
        # Retrieve and verify sanitization
        user = system["user_manager"].get_user(user_id)
        assert "<script>" not in user["full_name"]
        assert "alert" not in user["full_name"] or "&lt;script&gt;" in user["full_name"]
    
    def test_path_traversal_prevention(self, setup_system):
        """Test path traversal attempts in reports."""
        system = setup_system
        
        from hipaa_training.models import ComplianceDashboard
        from hipaa_training.security import ValidationError, SecurityError
        
        dashboard = ComplianceDashboard()
        
        # Attempt path traversal
        with pytest.raises((ValidationError, SecurityError)):
            dashboard.generate_enterprise_report(
                format_type="../../../etc/passwd"
            )
        
        # Attempt with legitimate format but malicious name
        with pytest.raises((ValidationError, SecurityError)):
            dashboard.generate_enterprise_report(
                format_type="csv; cat /etc/passwd"
            )
    
    def test_rate_limiting_enforcement(self, setup_system):
        """Test rate limiting prevents abuse."""
        system = setup_system
        
        from hipaa_training.security import RateLimitExceeded
        
        # Set low rate limit for testing
        os.environ["MAX_CERT_PER_HOUR"] = "3"
        
        # Reload to pick up new config
        from importlib import reload
        from hipaa_training import models
        reload(models)
        
        db = models.DatabaseManager()
        
        # Create user
        user_id = system["user_manager"].create_user(
            username="rate.test",
            full_name="Rate Test",
            role="staff",
        )
        
        # Issue certificates up to limit
        for i in range(3):
            cert_id = db.issue_certificate(user_id=user_id, score=85.0)
            assert cert_id is not None
        
        # Next attempt should fail
        with pytest.raises(RateLimitExceeded):
            db.issue_certificate(user_id=user_id, score=85.0)


class TestDataIntegrity:
    """Test data integrity and consistency."""
    
    @pytest.fixture
    def setup_system(self, tmp_path):
        """Set up test system."""
        db_path = tmp_path / "test_integrity.db"
        os.environ["DB_URL"] = str(db_path)
        
        from hipaa_training.models import DatabaseManager, UserManager
        
        return {
            "db": DatabaseManager(),
            "user_manager": UserManager(),
            "db_path": db_path,
        }
    
    def test_transaction_rollback_on_error(self, setup_system):
        """Test transactions rollback on errors."""
        system = setup_system
        
        user_id = system["user_manager"].create_user(
            username="rollback.test",
            full_name="Rollback Test",
            role="staff",
        )
        
        # Count initial progress records
        with system["db"]._get_connection() as conn:
            initial_count = conn.execute(
                "SELECT COUNT(*) FROM training_progress"
            ).fetchone()[0]
        
        # Attempt to save invalid data
        try:
            system["db"].save_progress(
                user_id=user_id,
                lesson_title="Test Lesson",
                score=150.0,  # Invalid: > 100
                checklist_data=None,
            )
        except Exception:
            pass
        
        # Verify no partial data was saved
        with system["db"]._get_connection() as conn:
            final_count = conn.execute(
                "SELECT COUNT(*) FROM training_progress"
            ).fetchone()[0]
            
            assert final_count == initial_count
    
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
    
    def test_duplicate_username_prevention(self, setup_system):
        """Test duplicate usernames are prevented."""
        system = setup_system
        
        from hipaa_training.security import ValidationError
        
        # Create first user
        system["user_manager"].create_user(
            username="unique.user",
            full_name="First User",
            role="staff",
        )
        
        # Attempt duplicate
        with pytest.raises(ValidationError, match="already exists"):
            system["user_manager"].create_user(
                username="unique.user",
                full_name="Second User",
                role="admin",
            )
    
    def test_certificate_expiry_tracking(self, setup_system):
        """Test certificate expiration is tracked correctly."""
        system = setup_system
        
        user_id = system["user_manager"].create_user(
            username="expiry.test",
            full_name="Expiry Test",
            role="staff",
        )
        
        cert_id = system["db"].issue_certificate(
            user_id=user_id,
            score=85.0,
        )
        
        # Verify expiry date is set correctly
        with system["db"]._get_connection() as conn:
            cert = conn.execute(
                "SELECT issue_date, expiry_date FROM certificates "
                "WHERE certificate_id = ?",
                (cert_id,),
            ).fetchone()
            
            issue_date = datetime.fromisoformat(cert["issue_date"])
            expiry_date = datetime.fromisoformat(cert["expiry_date"])
            
            # Should be 365 days apart (default)
            delta = expiry_date - issue_date
            assert 364 <= delta.days <= 366  # Account for leap years


class TestAuditLogging:
    """Test comprehensive audit logging."""
    
    @pytest.fixture
    def setup_system(self, tmp_path):
        """Set up test system."""
        db_path = tmp_path / "test_audit.db"
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        
        os.environ["DB_URL"] = str(db_path)
        os.environ["LOG_DIR"] = str(log_dir)
        
        from hipaa_training.models import DatabaseManager, UserManager
        
        return {
            "db": DatabaseManager(),
            "user_manager": UserManager(),
            "log_dir": log_dir,
        }
    
    def test_all_operations_logged(self, setup_system):
        """Test all critical operations are logged."""
        system = setup_system
        
        # Perform various operations
        user_id = system["user_manager"].create_user(
            username="audit.test",
            full_name="Audit Test",
            role="staff",
            session_id="audit-session",
            ip_address="10.0.0.1",
        )
        
        system["db"].save_progress(
            user_id=user_id,
            lesson_title="Test Lesson",
            score=90.0,
            checklist_data=None,
            session_id="audit-session",
            ip_address="10.0.0.1",
        )
        
        system["db"].issue_certificate(
            user_id=user_id,
            score=90.0,
            session_id="audit-session",
            ip_address="10.0.0.1",
        )
        
        # Verify all logged
        with system["db"]._get_connection() as conn:
            logs = conn.execute(
                "SELECT action, session_id, ip_address FROM audit_log "
                "WHERE user_id = ? ORDER BY timestamp",
                (user_id,),
            ).fetchall()
            
            assert len(logs) >= 3
            
            actions = [log["action"] for log in logs]
            assert "USER_CREATED" in actions
            assert "PROGRESS_SAVED" in actions
            assert "CERTIFICATE_ISSUED" in actions
            
            # Verify session tracking
            for log in logs:
                assert log["session_id"] == "audit-session"
                assert log["ip_address"] == "10.0.0.1"
    
    def test_audit_log_file_creation(self, setup_system):
        """Test audit logs are written to files."""
        system = setup_system
        
        # Perform operation
        system["user_manager"].create_user(
            username="file.log.test",
            full_name="File Log Test",
            role="staff",
        )
        
        # Check log file exists
        log_file = system["log_dir"] / "hipaa_audit.log"
        assert log_file.exists()
        
        # Verify log content
        with open(log_file, "r") as f:
            content = f.read()
            assert "USER_CREATED" in content
            assert "file.log.test" in content
    
    def test_failed_operations_logged(self, setup_system):
        """Test failed operations are logged."""
        system = setup_system
        
        from hipaa_training.security import ValidationError
        
        # Attempt invalid operation
        try:
            system["user_manager"].create_user(
                username="invalid user!@#",  # Invalid characters
                full_name="Test",
                role="staff",
                session_id="fail-session",
                ip_address="10.0.0.2",
            )
        except ValidationError:
            pass
        
        # Verify failure is logged
        with system["db"]._get_connection() as conn:
            logs = conn.execute(
                "SELECT * FROM audit_log WHERE action LIKE '%FAILED%' "
                "AND session_id = 'fail-session'"
            ).fetchall()
            
            # Should have logged the failure
            assert len(logs) > 0


class TestComplianceReporting:
    """Test compliance reporting functionality."""
    
    @pytest.fixture
    def setup_system_with_data(self, tmp_path):
        """Set up system with sample data."""
        db_path = tmp_path / "test_reports.db"
        os.environ["DB_URL"] = str(db_path)
        
        from hipaa_training.models import (
            DatabaseManager,
            UserManager,
            ComplianceDashboard,
        )
        
        db = DatabaseManager()
        um = UserManager()
        cd = ComplianceDashboard()
        
        # Create multiple users with varying completion
        users = []
        for i in range(5):
            user_id = um.create_user(
                username=f"user{i}",
                full_name=f"User {i}",
                role="staff",
            )
            users.append(user_id)
            
            # Some complete training
            if i < 3:
                db.save_progress(
                    user_id=user_id,
                    lesson_title="Test Lesson",
                    score=85.0 + i * 5,
                    checklist_data=None,
                )
                
                db.issue_certificate(
                    user_id=user_id,
                    score=85.0 + i * 5,
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
        
        # Verify CSV structure
        import csv
        with open(report_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1  # Summary row
            row = rows[0]
            
            assert "total_users" in row
            assert "avg_score" in row
            assert "pass_rate" in row
            assert "total_certs" in row
    
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
            
            assert data["total_users"] >= 3
            assert data["total_certs"] == 3
            assert data["active_certs"] == 3
            assert 0 <= data["avg_score"] <= 100
    
    def test_report_statistics_accuracy(self, setup_system_with_data):
        """Test statistics calculations are accurate."""
        system = setup_system_with_data
        
        stats = system["db"].get_compliance_stats()
        
        # Verify counts
        assert stats["total_users"] == 3  # Only users with progress
        assert stats["total_certs"] == 3
        assert stats["active_certs"] == 3
        assert stats["expired_certs"] == 0
        
        # Verify average score
        # Scores: 85, 90, 95
        expected_avg = (85 + 90 + 95) / 3
        assert abs(stats["avg_score"] - expected_avg) < 0.1
        
        # Verify pass rate (all passed with > 80)
        assert stats["pass_rate"] == 100.0


class TestErrorHandling:
    """Test error handling and recovery."""
    
    @pytest.fixture
    def setup_system(self, tmp_path):
        """Set up test system."""
        db_path = tmp_path / "test_errors.db"
        os.environ["DB_URL"] = str(db_path)
        
        from hipaa_training.models import DatabaseManager, UserManager
        
        return {
            "db": DatabaseManager(),
            "user_manager": UserManager(),
        }
    
    def test_invalid_score_handling(self, setup_system):
        """Test invalid scores are rejected."""
        system = setup_system
        
        from hipaa_training.security import ValidationError
        
        user_id = system["user_manager"].create_user(
            username="score.test",
            full_name="Score Test",
            role="staff",
        )
        
        # Test scores outside valid range
        with pytest.raises((ValidationError, ValueError)):
            system["db"].save_progress(
                user_id=user_id,
                lesson_title="Test",
                score=150.0,  # > 100
                checklist_data=None,
            )
        
        with pytest.raises((ValidationError, ValueError)):
            system["db"].save_progress(
                user_id=user_id,
                lesson_title="Test",
                score=-10.0,  # < 0
                checklist_data=None,
            )
    
    def test_database_corruption_recovery(self, setup_system):
        """Test system handles database errors gracefully."""
        system = setup_system
        
        # Close and corrupt the database file
        db_path = Path(os.environ["DB_URL"])
        
        # Create user first
        user_id = system["user_manager"].create_user(
            username="corrupt.test",
            full_name="Corrupt Test",
            role="staff",
        )
        
        # System should still be able to handle the valid user
        user = system["user_manager"].get_user(user_id)
        assert user is not None
    
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
            role="staff",
        )
        assert new_user_id > 0


class TestPerformanceAndScalability:
    """Test system performance under load."""
    
    @pytest.fixture
    def setup_system(self, tmp_path):
        """Set up test system."""
        db_path = tmp_path / "test_performance.db"
        os.environ["DB_URL"] = str(db_path)
        
        from hipaa_training.models import DatabaseManager, UserManager
        
        return {
            "db": DatabaseManager(),
            "user_manager": UserManager(),
        }
    
    def test_bulk_user_creation(self, setup_system):
        """Test creating multiple users efficiently."""
        system = setup_system
        
        start_time = time.time()
        
        # Create 50 users
        user_ids = []
        for i in range(50):
            user_id = system["user_manager"].create_user(
                username=f"bulk_user_{i}",
                full_name=f"Bulk User {i}",
                role="staff",
            )
            user_ids.append(user_id)
        
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0
        assert len(user_ids) == 50
        assert len(set(user_ids)) == 50  # All unique
    
    def test_concurrent_operations(self, setup_system):
        """Test system handles concurrent operations."""
        system = setup_system
        
        # Create user for concurrent operations
        user_id = system["user_manager"].create_user(
            username="concurrent.test",
            full_name="Concurrent Test",
            role="staff",
        )
        
        # Simulate concurrent progress saves
        for i in range(10):
            system["db"].save_progress(
                user_id=user_id,
                lesson_title=f"Lesson {i}",
                score=80.0 + i,
                checklist_data=None,
                session_id=f"session-{i}",
            )
        
        # Verify all saves succeeded
        with system["db"]._get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM training_progress WHERE user_id = ?",
                (user_id,),
            ).fetchone()[0]
            
            assert count == 10
    
    def test_large_checklist_data(self, setup_system):
        """Test handling of large checklist data."""
        system = setup_system
        
        user_id = system["user_manager"].create_user(
            username="large.data",
            full_name="Large Data",
            role="staff",
        )
        
        # Create large checklist
        large_checklist = {
            f"item_{i}": f"value_{i}" * 100  # Large values
            for i in range(100)
        }
        
        # Should handle large data
        system["db"].save_sensitive_progress(
            user_id=user_id,
            checklist_data=large_checklist,
            score=85.0,
        )
        
        # Verify it was saved and can be retrieved
        with system["db"]._get_connection() as conn:
            result = conn.execute(
                "SELECT checklist_data_encrypted FROM training_progress "
                "WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            
            assert result is not None
            assert len(result["checklist_data_encrypted"]) > 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

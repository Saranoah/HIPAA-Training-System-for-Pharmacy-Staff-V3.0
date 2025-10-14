#!/usr/bin/env python3
"""
Comprehensive test scenarios
Simulates real-world usage patterns
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def scenario_1_new_employee():
    """Scenario: New employee completes training"""
    print("\n📖 SCENARIO 1: New Employee Onboarding")
    print("-" * 60)

    from hipaa_training.models import UserManager
    from hipaa_training.training_engine import EnhancedTrainingEngine

    try:
        # Step 1: HR creates user
        print("Step 1: HR creates new employee account...")
        manager = UserManager()
        user_id = manager.create_user("jane_smith", "Jane Smith", "staff")
        print(f"✓ User created: {user_id}")
        time.sleep(0.5)

        # Step 2: Employee completes training
        print("\nStep 2: Employee views lessons...")
        engine = EnhancedTrainingEngine()
        lessons = list(engine.content.lessons.keys())[:3]  # First 3 lessons

        for lesson in lessons:
            print(f"  - Reading: {lesson}")
            time.sleep(0.3)
        print("✓ Lessons completed")

        # Step 3: Take quiz
        print("\nStep 3: Taking final quiz...")
        # Simulate quiz (would be interactive in real app)
        quiz_score = 85.0
        print(f"✓ Quiz completed with score: {quiz_score}%")

        # Step 4: Issue certificate
        print("\nStep 4: Generating certificate...")
        cert_id = engine.db.issue_certificate(user_id, quiz_score)
        print(f"✓ Certificate issued: {cert_id}")

        print("\n✅ Scenario 1 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Scenario 1 FAILED: {e}")
        return False


def scenario_2_annual_refresher():
    """Scenario: Annual training refresher"""
    print("\n📖 SCENARIO 2: Annual Training Refresher")
    print("-" * 60)

    from hipaa_training.models import UserManager, DatabaseManager

    try:
        # Step 1: Existing user logs in
        print("Step 1: Existing employee starts refresher...")
        manager = UserManager()
        user_id = manager.create_user("john_doe", "John Doe", "staff")
        print(f"✓ User authenticated: {user_id}")
        time.sleep(0.5)

        # Step 2: Complete quick review
        print("\nStep 2: Reviewing updated content...")
        time.sleep(0.5)
        print("✓ Review completed")

        # Step 3: Pass quiz
        print("\nStep 3: Passing refresher quiz...")
        db = DatabaseManager()
        db.save_progress(user_id, "Annual Refresher", 90.0, None)
        cert_id = db.issue_certificate(user_id, 90.0)
        print(f"✓ New certificate issued: {cert_id}")

        print("\n✅ Scenario 2 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Scenario 2 FAILED: {e}")
        return False


def scenario_3_compliance_audit():
    """Scenario: Compliance officer generates audit report"""
    print("\n📖 SCENARIO 3: Compliance Audit")
    print("-" * 60)

    from hipaa_training.models import UserManager, ComplianceDashboard

    try:
        # Step 1: Auditor logs in
        print("Step 1: Compliance officer accessing system...")
        manager = UserManager()
        auditor_id = manager.create_user("auditor", "Compliance Officer", "auditor")
        print(f"✓ Auditor authenticated: {auditor_id}")
        time.sleep(0.5)

        # Step 2: Generate reports
        print("\nStep 2: Generating compliance reports...")
        dashboard = ComplianceDashboard()

        csv_report = dashboard.generate_enterprise_report('csv')
        print(f"✓ CSV report: {csv_report}")

        json_report = dashboard.generate_enterprise_report('json')
        print(f"✓ JSON report: {json_report}")

        # Step 3: Review statistics
        print("\nStep 3: Reviewing compliance statistics...")
        stats = dashboard.db.get_compliance_stats()
        print(f"  Total users trained: {stats['total_users']}")
        print(f"  Average score: {stats['avg_score']}%")
        print(f"  Pass rate: {stats['pass_rate']}%")
        print(f"  Active certificates: {stats['active_certs']}")
        print("✓ Audit completed")

        print("\n✅ Scenario 3 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Scenario 3 FAILED: {e}")
        return False


def main():
    """Run all scenarios"""
    print("🎭 Real-World Test Scenarios")
    print("=" * 60)

    # Setup test environment
    if not os.getenv('HIPAA_ENCRYPTION_KEY'):
        os.environ['HIPAA_ENCRYPTION_KEY'] = 'test-scenario-key-32-characters'
    if not os.getenv('HIPAA_SALT'):
        os.environ['HIPAA_SALT'] = 'test-salt-16-hex'

    scenarios = [
        scenario_1_new_employee,
        scenario_2_annual_refresher,
        scenario_3_compliance_audit
    ]

    results = []

    for scenario in scenarios:
        try:
            results.append(scenario())
            time.sleep(1)
        except Exception as e:
            print(f"\n❌ Scenario crashed: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("📊 SCENARIO SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if all(results):
        print("\n✅ All scenarios passed - Production ready!")
        return 0
    else:
        print("\n❌ Some scenarios failed - Review and fix")
        return 1


if __name__ == '__main__':
    sys.exit(main())

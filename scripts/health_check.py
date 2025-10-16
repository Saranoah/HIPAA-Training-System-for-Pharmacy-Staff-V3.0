#!/usr/bin/env python3
"""
HIPAA Training System - Health Check Script
Run this script to verify system health and compliance status
"""
import os
import sys
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path so we can import hipaa_training
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def health_check():
    """Comprehensive system health check"""
    checks = {}

    print("🏥 HIPAA Training System - Health Check")
    print("=" * 50)

    # Check database
    try:
        db_path = 'data/hipaa_training.db'
        if not Path(db_path).exists():
            checks['database'] = False
            print(f"📊 Database: ❌ NOT FOUND at {db_path}")
        else:
            conn = sqlite3.connect(db_path)
            integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
            checks['database'] = integrity == 'ok'
            print(f"📊 Database: {'✅ OK' if checks['database'] else '❌ CORRUPTED'}")

            # Check user count
            try:
                user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
                print(f"   👥 Users: {user_count}")
            except sqlite3.OperationalError:
                print("   ⚠️  Users table not found (run main.py --setup-only)")

            # Check training completion
            try:
                training_count = conn.execute(
                    'SELECT COUNT(*) FROM training_progress WHERE quiz_score IS NOT NULL'
                ).fetchone()[0]
                print(f"   📚 Training Sessions: {training_count}")
            except sqlite3.OperationalError:
                print("   ⚠️  Training table not found")

            # Check certificate count
            try:
                cert_count = conn.execute('SELECT COUNT(*) FROM certificates').fetchone()[0]
                print(f"   🎓 Certificates Issued: {cert_count}")
            except sqlite3.OperationalError:
                print("   ⚠️  Certificate table not found")

            conn.close()
    except Exception as e:
        checks['database'] = False
        print(f"📊 Database: ❌ ERROR - {e}")

    # Check content files
    content_files = ['lessons.json', 'quiz_questions.json', 'checklist_items.json']
    missing_files = []
    for f in content_files:
        if not Path(f'content/{f}').exists():
            missing_files.append(f)

    checks['content'] = len(missing_files) == 0
    if checks['content']:
        print(f"📚 Content Files: ✅ OK")
        # Validate JSON structure
        for f in content_files:
            try:
                with open(f'content/{f}', 'r') as file:
                    json.load(file)
                print(f"   ✓ {f} - Valid JSON")
            except json.JSONDecodeError as e:
                print(f"   ❌ {f} - Invalid JSON: {e}")
                checks['content'] = False
    else:
        print(f"📚 Content Files: ❌ MISSING: {', '.join(missing_files)}")

    # Check directories
    directories = {
        'certificates': 'Certificate storage',
        'reports': 'Compliance reports',
        'evidence': 'Evidence files',
        'data': 'Database files',
        'logs': 'Audit logs'
    }

    for directory, description in directories.items():
        exists = Path(directory).exists()
        print(f"📁 {directory}/: {'✅ EXISTS' if exists else '❌ MISSING'} ({description})")

    # Check encryption key
    encryption_key = os.getenv('HIPAA_ENCRYPTION_KEY')
    checks['encryption'] = bool(encryption_key and len(encryption_key) >= 32)
    if checks['encryption']:
        print(f"🔐 Encryption Key: ✅ SET (length: {len(encryption_key)} chars)")
    else:
        print(f"🔐 Encryption Key: ❌ MISSING or TOO SHORT")
        print("   Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'")

    # Check salt
    salt = os.getenv('HIPAA_SALT')
    if salt:
        print(f"🧂 Salt: ✅ SET")
    else:
        print(f"🧂 Salt: ⚠️  NOT SET (will use random - decryption may fail on restart)")

)")

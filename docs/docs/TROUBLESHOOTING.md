# HIPAA Training System V3.0 - Troubleshooting Guide

Common issues and solutions for the HIPAA Training System.

---

## 🔴 Installation Issues

### Error: "No module named 'hipaa_training'"
**Cause:** Python can't find the package.  
**Solution:**
```bash
cd /path/to/hipaa-training-v3
ls hipaa_training/
python main.py
```

### Error: "HIPAA_ENCRYPTION_KEY environment variable must be set"

**Cause:** Required encryption key not configured.
**Solution:**

```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Linux/macOS
export HIPAA_ENCRYPTION_KEY='your-generated-key-here'

# Windows
set HIPAA_ENCRYPTION_KEY=your-generated-key-here

# Or add to .env
echo 'HIPAA_ENCRYPTION_KEY="your-generated-key-here"' >> .env
```

### Error: "ModuleNotFoundError: No module named 'cryptography'"

**Cause:** Dependencies not installed.
**Solution:**

```bash
pip install -r requirements.txt
pip install cryptography rich pytest pytest-cov
```

### Error: "Permission denied" when creating directories

**Cause:** Insufficient permissions.
**Solution:**

```bash
sudo chown -R $USER:$USER .
chmod 755 .
python main.py --setup-only
```

---

## 🔴 Runtime Errors

### Error: "Database is locked"

**Cause:** Another process is accessing the database or improper shutdown.
**Solution:**

```bash
ps aux | grep python
kill -9 <process_id>
rm data/hipaa_training.db-shm
rm data/hipaa_training.db-wal
python main.py
```

### Error: "Failed to decrypt data"

**Cause:** Encryption key changed or data corrupted.
**Solution:**

```bash
# Restore original key if changed
rm data/hipaa_training.db
python main.py --setup-only

# Restore from backup if corrupted
cp backups/hipaa_training_YYYYMMDD_HHMMSS.db.gz .
gunzip hipaa_training_YYYYMMDD_HHMMSS.db.gz
mv hipaa_training_YYYYMMDD_HHMMSS.db data/hipaa_training.db
```

### Error: "Invalid user ID"

**Cause:** User doesn't exist in database.
**Solution:**

```bash
sqlite3 data/hipaa_training.db "SELECT * FROM users;"
python main.py  # create new user
```

### Quiz shows incorrect answers

**Cause:** Old version with randomization bug.
**Solution:**

```bash
git pull origin main
# or replace training_engine.py with fixed version
# ensure options = q['options'].copy()
```

---

## 🔴 Test Failures

### Error: "No module named 'conftest'"

**Cause:** Missing pytest configuration file.
**Solution:**

```bash
cat > tests/conftest.py << 'EOF'
import pytest, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ['HIPAA_ENCRYPTION_KEY'] = 'test-key-32-chars'
os.environ['HIPAA_SALT'] = 'test-salt-hex'
EOF
pytest tests/ -v
```

### Error: "fixture 'security_manager' not found"

**Cause:** Test file missing proper imports or fixtures.
**Solution:**

```python
import pytest
from unittest.mock import patch

@pytest.fixture
def security_manager():
    with patch.dict('os.environ', {
        'HIPAA_ENCRYPTION_KEY': 'test-key-32-chars',
        'HIPAA_SALT': 'test-salt-hex'
    }):
        from hipaa_training.security import SecurityManager
        return SecurityManager()
```

### Tests pass locally but fail in CI/CD

**Cause:** Environment differences.
**Solution:**

```yaml
env:
  HIPAA_ENCRYPTION_KEY: test-key-for-ci
  HIPAA_SALT: test-salt-12345678
python-version: ['3.9', '3.10', '3.11', '3.12']
```

---

## 🔴 Content Issues

### Error: "Lesson 'X' not found"

**Cause:** Content files missing or corrupted.
**Solution:**

```bash
ls -la content/
python -m json.tool content/lessons.json
rm content/lessons.json
python main.py
```

### Wrong encoding

**Cause:** Non-UTF-8 characters.
**Solution:**

```bash
iconv -f ISO-8859-1 -t UTF-8 content/lessons.json > content/lessons_utf8.json
mv content/lessons_utf8.json content/lessons.json
```

---

## 🔴 Performance Issues

### Slow database queries

**Cause:** Missing indexes or large dataset.
**Solution:**

```bash
sqlite3 data/hipaa_training.db ".schema"
python main.py --setup-only
sqlite3 data/hipaa_training.db "CREATE INDEX idx_user_id ON training_progress(user_id);"
```

### Application freezes during encryption

**Cause:** Large files encrypted in memory.
**Solution:**

```python
self.security.encrypt_file(evidence_path, dest_path)
# NOT: encrypted = self.security.cipher.encrypt(file_data)
```

---

## 🔴 Logging Issues

### No audit logs

**Cause:** Directory missing or permissions.
**Solution:**

```bash
mkdir -p logs
chmod 700 logs
python main.py
```

### Log files too large

**Solution:**

```python
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler('logs/hipaa_audit.log', maxBytes=10*1024*1024, backupCount=5)
```

---

## 🔴 Security Issues

### Random salt warning

```bash
python -c 'import secrets; print(secrets.token_hex(16))'
echo 'HIPAA_SALT="generated-salt-here"' >> .env
export HIPAA_SALT='generated-salt-here'
```

### Evidence files can't decrypt

```bash
# Must use same HIPAA_ENCRYPTION_KEY & HIPAA_SALT used during encryption
```

---

## 🔴 Backup/Restore Issues

### Backup fails: SQLite not found

```bash
sudo apt-get install sqlite3  # Linux
brew install sqlite3          # macOS
# Windows: download from https://www.sqlite.org/download.html
```

### Restore fails: corrupted backup

```bash
sqlite3 data/hipaa_training.db ".recover" | sqlite3 recovered.db
gunzip -c backups/hipaa_training_YYYYMMDD_HHMMSS.db.gz > data/hipaa_training.db
```

### Automated backups not running

```bash
crontab -e
0 2 * * * /full/path/to/scripts/backup_database.sh >> /var/log/hipaa_backup.log 2>&1
chmod +x scripts/backup_database.sh
./scripts/backup_database.sh
```

---

## 🔴 Certificate Issues

### Certificate not issued

```bash
sqlite3 data/hipaa_training.db "SELECT user_id, quiz_score FROM training_progress WHERE quiz_score IS NOT NULL;"
sqlite3 data/hipaa_training.db << EOF
INSERT INTO certificates (user_id, certificate_id, score, issue_date, expiry_date)
VALUES (1, 'manual-cert-$(uuidgen)', 85.0, datetime('now'), datetime('now', '+365 days'));
EOF
```

### Certificate expired but training valid

```bash
sqlite3 data/hipaa_training.db "UPDATE certificates SET expiry_date = datetime('now', '+365 days') WHERE certificate_id = 'YOUR-CERT-ID';"
```

---

## 🔴 Docker Issues

### Build fails

```bash
ls Dockerfile
docker build -t hipaa-training:v3 .
cat .dockerignore
```

### Container exits

```bash
docker run -it --rm \
  -e HIPAA_ENCRYPTION_KEY="your-key-here" \
  -e HIPAA_SALT="your-salt-here" \
  hipaa-training:v3
```

### Can't access database

```bash
docker run -it --rm \
  -e HIPAA_ENCRYPTION_KEY="your-key" \
  -e HIPAA_SALT="your-salt" \
  -v $(pwd)/data:/app/data \
  hipaa-training:v3
```

---

## 🔴 Import Errors

### "cannot import name 'X'"

```python
__all__ = ['CLI','DatabaseManager','UserManager','ComplianceDashboard','SecurityManager','EnhancedTrainingEngine','ContentManager']
from .security import SecurityManager
from .models import DatabaseManager, UserManager, ComplianceDashboard
from .content_manager import ContentManager
from .training_engine import EnhancedTrainingEngine
from .cli import CLI
```

---

## 🔴 Platform-Specific Issues

* Windows: Use `os.path.join` or `pathlib`
* chmod: Unix only, check `platform.system()`
* macOS: Grant terminal full disk access

---

## 🛠️ Debug, Health Check & Diagnostics

```bash
python main.py --debug
export DEBUG=true
python main.py
python scripts/health_check.py
python --version
pip list | grep -E "cryptography|rich|pytest"
sqlite3 data/hipaa_training.db ".schema"
tail -n 100 logs/hipaa_audit.log
pytest tests/ -v --tb=long
```

---

 ## 🚑 Emergency Recovery

```bash
mkdir emergency_backup
cp -r data/ evidence/ logs/ emergency_backup/
rm -rf hipaa_training/__pycache__ data/hipaa_training.db logs/*
pip uninstall -y cryptography rich pytest
pip install -r requirements.txt
python main.py --setup-only
cp emergency_backup/data/hipaa_training.db data/
python scripts/health_check.py
```

---

## 📝 Known Issues & Preventive Measures

* Evidence files >5MB rejected
* No web interface (planned V4.0)
* Email notifications not sent

**Preventive Measures:**

* Regular backups via cron
* Monitor logs weekly
* Test restores monthly
* Keep updated: `git pull`, `pip install -r requirements.txt --upgrade`
* Weekly health checks: `python scripts/health_check.py`

---

## 📚 Resources

* [HIPAA Guidance](https://www.hhs.gov/hipaa)
* [Python Docs](https://docs.python.org/3/)
* [SQLite Docs](https://www.sqlite.org/docs.html)
* [Cryptography Library](https://cryptography.io/)



**Last Updated:** 2025-01-11  
**Version:** 3.0

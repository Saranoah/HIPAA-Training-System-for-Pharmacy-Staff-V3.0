# 🚀 HIPAA Training System V3.0 - Setup Guide

## 📋 Pre-Deployment Checklist

Before deploying to production, ensure ALL these issues are fixed:

### ✅ Critical Fixes Applied

1. **Database Context Manager** - Fixed broken `_get_connection()` method
2. **Missing Import** - Added `sqlite3` import to `security.py`
3. **Salt Encoding Bug** - Fixed encryption setup
4. **Quiz Randomization** - Fixed answer validation bug
5. **Cross-Platform Permissions** - Windows compatibility
6. **Environment Variables** - Added validation
7. **Path Traversal Protection** - Secured file uploads
8. **Chunked Encryption** - Memory-efficient file handling

---

## 🔧 Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/Saranoah/HIPAA-Training-System-for-Pharmacy-Staff-V3.0.git
cd HIPAA-Training-System-for-Pharmacy-Staff-V3.0
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy template
cp .env.example .env

# Generate secure keys
python -c "import secrets; print('HIPAA_ENCRYPTION_KEY=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('HIPAA_SALT=' + secrets.token_hex(16))" >> .env

# Edit .env and verify the keys were added
cat .env
```

### 5. Setup Production Environment

```bash
# Check environment configuration
python main.py --check-env

# Setup directories and database
python main.py --setup-only

# Verify setup
ls -la data/ logs/ reports/ certificates/ evidence/
```

### 6. Run Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=hipaa_training --cov-report=html
```

---

## 🔒 Security Configuration

### Required Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `HIPAA_ENCRYPTION_KEY` | **YES** | Encryption key for sensitive data | `abc123...` (32+ chars) |
| `HIPAA_SALT` | **YES** | Salt for key derivation | `a1b2c3d4...` (32 hex chars) |
| `DB_URL` | No | Database path | `data/hipaa_training.db` |
| `PASS_THRESHOLD` | No | Quiz passing score (%) | `80` |
| `TRAINING_EXPIRY_DAYS` | No | Certificate validity | `365` |

### Generate Secure Keys

```bash
# Encryption key
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Salt (hexadecimal)
python -c 'import secrets; print(secrets.token_hex(16))'
```

### Secure File Permissions (Linux/macOS)

```bash
# Database
chmod 600 data/hipaa_training.db

# Directories
chmod 700 data/ logs/ reports/ certificates/ evidence/

# Verify
ls -la data/ logs/
```

---

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t hipaa-training:v3.0 .
```

### Run Container

```bash
docker run -it --rm \
  -e HIPAA_ENCRYPTION_KEY="your-secure-key" \
  -e HIPAA_SALT="your-secure-salt" \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  hipaa-training:v3.0
```

### Docker Compose

```yaml
version: '3.8'

services:
  hipaa-training:
    build: .
    environment:
      - HIPAA_ENCRYPTION_KEY=${HIPAA_ENCRYPTION_KEY}
      - HIPAA_SALT=${HIPAA_SALT}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./reports:/app/reports
    restart: unless-stopped
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Test Specific Module

```bash
pytest tests/test_user_manager.py -v
pytest tests/test_training_engine.py -v
pytest tests/test_security_manager.py -v
```

### Test Coverage

```bash
# Generate HTML coverage report
pytest --cov=hipaa_training --cov-report=html

# Open report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Security Scan

```bash
# Run Bandit security scanner
bandit -r hipaa_training/ main.py -f json -o security-report.json

# View results
cat security-report.json | python -m json.tool
```

---

## 🚀 Running the Application

### Interactive Mode (Default)

```bash
python main.py
```

### Command-Line Options

```bash
# Show version
python main.py --version

# Check environment configuration
python main.py --check-env

# Setup only (don't start CLI)
python main.py --setup-only

# Debug mode (verbose output)
python main.py --debug
```

---

## 📊 Usage Workflow

### For New Users

1. **Create User Account**
   - Select option 1: "Create New User"
   - Enter username, full name, and role

2. **Start Training**
   - Select option 2: "Start Training"
   - Enter your user ID
   - Complete all 13 lessons
   - Pass mini-quizzes (70%+ required)
   - Complete final assessment (80%+ to pass)

3. **Complete Checklist**
   - Select option 3: "Complete Compliance Checklist"
   - Answer 15 checklist items
   - Upload evidence files (optional)

4. **Generate Report**
   - Select option 4: "Generate Compliance Report"
   - Choose format (CSV or JSON)
   - Report saved to `reports/` directory

---

## 🔍 Troubleshooting

### Error: "HIPAA_ENCRYPTION_KEY environment variable must be set"

**Solution:**
```bash
# Generate and set key
export HIPAA_ENCRYPTION_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
export HIPAA_SALT=$(python -c 'import secrets; print(secrets.token_hex(16))')
```

### Error: "Module 'sqlite3' has no attribute 'connect'"

**Solution:** This means Python wasn't compiled with SQLite support (rare). Install full Python version or use PostgreSQL.

### Error: "Permission denied" on directories

**Solution:**
```bash
# Linux/macOS
sudo chown -R $USER:$USER data/ logs/ reports/
chmod 700 data/ logs/ reports/

# Windows - run as Administrator
icacls data /grant %USERNAME%:F /T
```

### Error: "Failed to initialize database"

**Solution:**
```bash
# Remove corrupted database and reinitialize
rm data/hipaa_training.db
python main.py --setup-only
```

### Quiz answers always wrong

**Cause:** This was the randomization bug (now fixed).

**Verify Fix:**
```python
# Check this in training_engine.py
options = q['options'].copy()  # Must have .copy()!
```

---

## 📈 Production Deployment Best Practices

### 1. Database Backups

```bash
# Create backup script
cat > scripts/backup_database.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp data/hipaa_training.db backups/hipaa_training_${TIMESTAMP}.db
echo "Backup created: backups/hipaa_training_${TIMESTAMP}.db"
EOF

chmod +x scripts/backup_database.sh

# Run daily via cron
crontab -e
# Add: 0 2 * * * /path/to/scripts/backup_database.sh
```

### 2. Log Rotation

Logs automatically rotate at 10MB with 5 backup files.

Manual rotation:
```bash
# Archive old logs
tar -czf logs_archive_$(date +%Y%m%d).tar.gz logs/*.log.*
mv logs_archive_*.tar.gz archives/
```

### 3. Certificate Cleanup

```bash
# Remove expired certificates (run monthly)
sqlite3 data/hipaa_training.db << 'EOF'
DELETE FROM certificates 
WHERE expiry_date < datetime('now') 
AND revoked = FALSE;
EOF
```

### 4. Monitoring

```bash
# Health check script
cat > scripts/health_check.py << 'EOF'
#!/usr/bin/env python3
import sys
from hipaa_training.models import DatabaseManager

try:
    db = DatabaseManager()
    stats = db.get_compliance_stats()
    print(f"✓ System healthy - {stats['total_users']} users")
    sys.exit(0)
except Exception as e:
    print(f"✗ System unhealthy: {e}")
    sys.exit(1)
EOF

chmod +x scripts/health_check.py
```

---

## 🔐 HIPAA Compliance Checklist

- [ ] Encryption keys stored securely (not in code)
- [ ] Database has proper access controls (chmod 600)
- [ ] Audit logs enabled and retained for 6 years
- [ ] No PHI/PII in version control
- [ ] Regular backups scheduled
- [ ] Access logs reviewed monthly
- [ ] User authentication enforced
- [ ] Evidence files encrypted at rest
- [ ] Network traffic encrypted (if web version)
- [ ] Incident response plan documented

---

## 📞 Support

- **GitHub Issues:** [Report bugs](https://github.com/Saranoah/HIPAA-Training-System-for-Pharmacy-Staff-V3.0/issues)
- **Documentation:** See `docs/` directory
- **Email:** [Your email]

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 🎯 What's Fixed in V3.0.1

| Issue | Status | Priority |
|-------|--------|----------|
| Context manager bug | ✅ Fixed | CRITICAL |
| Missing sqlite3 import | ✅ Fixed | CRITICAL |
| Salt encoding error | ✅ Fixed | CRITICAL |
| Quiz randomization | ✅ Fixed | CRITICAL |
| Default encryption key | ✅ Fixed | CRITICAL |
| Cross-platform chmod | ✅ Fixed | HIGH |
| Database indexes | ✅ Added | HIGH |
| Path traversal | ✅ Fixed | HIGH |
| Log rotation | ✅ Added | MEDIUM |
| Chunked encryption | ✅ Added | MEDIUM |

---

**Version:** 3.0.1  
**Last Updated:** 2025-01-11  
**Status:** Production Ready ✅

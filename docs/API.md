# HIPAA Training System V3.0 - API Documentation

This document describes the internal API and module structure of the HIPAA Training System.

---

## 📦 Module Structure

```
hipaa_training/
├── __init__.py          # Package initialization and exports
├── cli.py               # Command-line interface
├── models.py            # Database models and business logic
├── security.py          # Security and encryption functions
├── training_engine.py   # Training content delivery
└── content_manager.py   # Content loading and validation
```

---

## 🔧 Core Modules

### `models.py`

#### **Config Class**

Configuration settings loaded from environment variables.

```python
class Config:
    DB_PATH: str                    # Database file path
    PASS_THRESHOLD: int             # Quiz passing score (default: 80)
    TRAINING_EXPIRY_DAYS: int       # Certificate validity (default: 365)
    AUDIT_RETENTION_YEARS: int      # Log retention period (default: 6)
    MINI_QUIZ_THRESHOLD: int        # Mini-quiz passing score (default: 70)
    ENCRYPTION_KEY: str             # Encryption key (REQUIRED)
```

**Environment Variables:**

* `DB_URL` – Database path
* `PASS_THRESHOLD` – Quiz passing percentage
* `TRAINING_EXPIRY_DAYS` – Certificate validity in days
* `HIPAA_ENCRYPTION_KEY` – **REQUIRED** encryption key
* `HIPAA_SALT` – Salt for key derivation

---

### **DatabaseManager Class**

Manages all database operations.

**Methods:**

```python
__init__(db_path: str = Config.DB_PATH) -> None
```

Initialize database connection and create tables.

```python
save_progress(user_id: int, lesson_title: str, score: Optional[float],
              checklist_data: Optional[Dict]) -> None
```

Save training progress for a user.

**Parameters:**

* `user_id` – User identifier
* `lesson_title` – Name of completed lesson
* `score` – Quiz score (optional)
* `checklist_data` – Checklist responses (optional)

---

```python
save_sensitive_progress(user_id: int, checklist_data: Dict,
                        score: Optional[float]) -> None
```

Save progress with encrypted sensitive data.

```python
issue_certificate(user_id: int, score: float) -> str
```

Issue a training certificate.
**Returns:** Certificate UUID

```python
get_compliance_stats() -> Dict
```

Retrieve compliance statistics for reporting.
**Returns:**

```json
{
  "total_users": int,
  "avg_score": float,
  "pass_rate": float,
  "total_certs": int,
  "active_certs": int,
  "expired_certs": int
}
```

---

### **UserManager Class**

Manages user creation and validation.

**Methods:**

```python
create_user(username: str, full_name: str, role: str) -> int
```

Create a new user.

**Parameters:**

* `username` – Unique username (sanitized)
* `full_name` – User’s full name
* `role` – One of: `'admin'`, `'staff'`, `'auditor'`

**Returns:** User ID
**Raises:**
`ValueError` – Invalid role or duplicate username

```python
user_exists(user_id: int) -> bool
```

Check if a user exists.

```python
get_user(user_id: int) -> Optional[Dict]
```

Get user details by ID.
**Returns:**

```json
{
  "id": int,
  "username": str,
  "full_name": str,
  "role": str,
  "created_at": str
}
```

---

### **ComplianceDashboard Class**

Generates compliance reports.

**Methods:**

```python
generate_enterprise_report(format_type: str) -> str
```

Generate compliance report in CSV or JSON format.

**Parameters:**

* `format_type` – Either `'csv'` or `'json'`

**Returns:** Generated filename
**Raises:**
`ValueError` – Invalid format type

---

### `security.py`

#### **SecurityManager Class**

Handles encryption, decryption, and audit logging.

**Methods:**

```python
encrypt_data(data: str) -> str
```

Encrypt sensitive string data using Fernet.
**Parameters:**

* `data` – Plain text string
  **Returns:** Base64-encoded encrypted string

```python
decrypt_data(encrypted_data: str) -> str
```

Decrypt encrypted string data.
**Parameters:**

* `encrypted_data` – Base64-encoded encrypted string
  **Returns:** Plain text string

```python
encrypt_file(input_path: str, output_path: str) -> None
```

Encrypt a file in chunks (memory-efficient for large files).

```python
decrypt_file(input_path: str, output_path: str) -> None
```

Decrypt a file that was encrypted in chunks.

```python
log_action(user_id: int, action: str, details: str) -> None
```

Log an action to both file and database for HIPAA audit trail.

**Parameters:**

* `user_id` – User performing action
* `action` – Action type (e.g., `"USER_CREATED"`, `"QUIZ_COMPLETED"`)
* `details` – Additional details about the action

---

### `training_engine.py`

#### **EnhancedTrainingEngine Class**

Manages training delivery and assessment.

**Methods:**

```python
display_lesson(user_id: int, lesson_title: str) -> None
```

Display a lesson with formatted output.

```python
adaptive_quiz(user_id: int) -> float
```

Conduct adaptive final quiz with randomized questions.
**Returns:** Score as percentage (0–100)

```python
complete_enhanced_checklist(user_id: int) -> None
```

Guide user through compliance checklist with evidence upload.

---

### `content_manager.py`

#### **ContentManager Class**

Loads and validates training content.

**Attributes:**

* `lessons`: `Dict[str, Dict]` – Lesson content
* `quiz_questions`: `List[Dict]` – Quiz questions
* `checklist_items`: `List[Dict]` – Checklist items

**Methods:**

```python
get_lesson(lesson_title: str) -> Dict
```

Get a specific lesson by title.

```python
get_all_lessons() -> List[str]
```

Get list of all lesson titles.

```python
get_quiz_question_count() -> int
```

Get total number of quiz questions.

```python
get_checklist_item_count() -> int
```

Get total number of checklist items.

---

### `cli.py`

#### **CLI Class**

Command-line interface for the training system.

**Methods:**

```python
run() -> None
```

---

## 🗄️ Database Schema

### `users` Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `training_progress` Table

```sql
CREATE TABLE training_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    lesson_title TEXT,
    quiz_score REAL,
    checklist_data TEXT,  -- May be encrypted
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
```

### `certificates` Table

```sql
CREATE TABLE certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    certificate_id TEXT UNIQUE NOT NULL,
    score REAL NOT NULL,
    issue_date TIMESTAMP NOT NULL,
    expiry_date TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP,
    revoked_reason TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
```

### `audit_log` Table

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);
```

---

## 🔐 Security Features

### **Encryption**

* Algorithm: Fernet (symmetric encryption)
* Key Derivation: PBKDF2-HMAC-SHA256 with 100,000 iterations
* Data at Rest: Checklist responses, evidence files
* Data in Transit: N/A (CLI application)

### **Audit Logging**

* All user actions logged
* Logs retained for 6 years (configurable)
* Dual logging: file + database
* Rotating log files (10 MB max, 5 backups)

### **Access Controls**

* Role-based access (`admin` / `staff` / `auditor`)
* Input sanitization to prevent injection
* Session management *(future enhancement)*

---

## 📊 Usage Examples

### Create a User

```python
from hipaa_training.models import UserManager

manager = UserManager()
user_id = manager.create_user("jdoe", "John Doe", "staff")
print(f"Created user ID: {user_id}")
```

### Encrypt Data

```python
from hipaa_training.security import SecurityManager

security = SecurityManager()
encrypted = security.encrypt_data("Sensitive PHI")
decrypted = security.decrypt_data(encrypted)
assert decrypted == "Sensitive PHI"
```

### Generate Report

```python
from hipaa_training.models import ComplianceDashboard

dashboard = ComplianceDashboard()
filename = dashboard.generate_enterprise_report('json')
print(f"Report saved: {filename}")
```

---

## 🧪 Testing

Run tests with pytest:

```bash
pytest tests/ -v
pytest tests/ --cov=hipaa_training --cov-report=html
```

---

## 📝 Notes

* All methods that access PHI log actions via `SecurityManager`
* Database uses parameterized queries to prevent SQL injection
* Files are encrypted in 64 KB chunks for memory efficiency
* Passwords/keys should **never** be hardcoded

**Last Updated:** 2025-01-11
**Version:** 3.0

---

#!/usr/bin/env python3
"""
HIPAA Training System - Project Setup Script
Automatically creates directory structure and essential GitHub files
"""

import os
import stat
from pathlib import Path

def create_project_structure():
    """Create the complete project directory structure"""
    directories = [
        '.github/workflows',
        '.devcontainer',
        'hipaa_training',
        'tests',
        'content',
        'docs',
        'scripts',
        'data',
        'reports',
        'certificates',
        'evidence'
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_file(path, content):
    """Create a file with the given content"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created file: {path}")

def main():
    print("🏥 HIPAA Training System V3.0 - Project Setup")
    print("=" * 50)

    # Create directory structure
    create_project_structure()

    # Create essential configuration files
    create_file('.gitignore', '''__pycache__/
*.py[cod]
*$py.class
dist/
build/
*.egg-info/
eggs/
.eggs/
.env
.venv
env/
venv/
data/*.db
data/*.sqlite3
*.log
logs/
backup/
*.backup
.vscode/
.idea/
*.swp
*.swo
evidence/
reports/
certificates/
''')

    create_file('.env.example', '''# HIPAA Training System V3.0 - Environment Configuration
HIPAA_ENCRYPTION_KEY=your-secure-key-here-32-characters-minimum
HIPAA_SALT=your-encryption-salt-here
DB_URL=sqlite:///data/hipaa_training.db
PASS_THRESHOLD=80
TRAINING_EXPIRY_DAYS=365
AUDIT_RETENTION_YEARS=6
DB_PASSWORD=your-postgres-password
QUIZ_QUESTION_COUNT=10
''')

    create_file('requirements.txt', '''cryptography>=3.4.8
sqlalchemy>=1.4.23
alembic>=1.7.1
python-dotenv>=0.19.0
python-dateutil>=2.8.2
psycopg2-binary>=2.9.3
colorama>=0.4.4
rich>=12.5.1
pyttsx3>=2.90; sys_platform != 'linux'
speechrecognition>=3.8.1
fastapi>=0.68.0
uvicorn>=0.15.0
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
flake8>=6.0.0
bandit>=1.7.5
''')

    create_file('content/lessons.json', '''{
    "Sample Lesson": {
        "content": "This is a sample lesson for HIPAA compliance training.",
        "key_points": ["Point 1: Protect patient data.", "Point 2: Follow HIPAA rules."],
        "comprehension_questions": [
            {
                "question": "What is the main goal of HIPAA?",
                "options": ["Protect patient data", "Increase hospital revenue", "Simplify billing", "Reduce staff training"],
                "correct_index": 0
            }
        ]
    }
}
''')

    create_file('content/quiz_questions.json', '''[
    {
        "question": "What is the main goal of HIPAA?",
        "options": ["Protect patient data", "Increase hospital revenue", "Simplify billing", "Reduce staff training"],
        "correct_index": 0,
        "explanation": "HIPAA ensures the protection of patient health information."
    }
]
''')

    create_file('content/checklist_items.json', '''[
    {
        "text": "Verify Business Associate Agreements",
        "category": "Compliance",
        "validation_hint": "Upload signed BAA document"
    }
]
''')

    print("\n🎉 Project setup completed successfully!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and set secure values")
    print("2. Run: pip install -r requirements.txt")
    print("3. Run: scripts/setup_production.sh")
    print("4. Run: git init")
    print("5. Run: git add .")
    print("6. Run: git commit -m 'Initial commit: HIPAA Training System V3.0'")
    print("7. Create GitHub repository and push")
    print("8. Run: python main.py")

if __name__ == "__main__":
    main()

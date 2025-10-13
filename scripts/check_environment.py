#!/usr/bin/env python3
"""
Environment validation script
Checks all required environment variables and dependencies
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ required")
        return False
    
    print("✓ Python version OK")
    return True


def check_environment_variables():
    """Check required environment variables"""
    required_vars = {
        'HIPAA_ENCRYPTION_KEY': 'Encryption key for PHI data',
        'HIPAA_SALT': 'Salt for key derivation'
    }
    
    all_set = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            print(f"❌ {var} not set ({description})")
            all_set = False
        else:
            length = len(value)
            print(f"✓ {var} set (length: {length})")
            
            # Validate minimum length
            if var == 'HIPAA_ENCRYPTION_KEY' and length < 32:
                print(f"  ⚠️  Warning: {var} should be at least 32 characters")
    
    return all_set


def check_dependencies():
    """Check required Python packages"""
    required_packages = {
        'cryptography': '41.0.0',
        'rich': '13.0.0',
        'pytest': '7.4.0'
    }
    
    all_installed = True
    
    try:
        import pkg_resources
    except ImportError:
        print("❌ setuptools not installed")
        return False
    
    for package, min_version in required_packages.items():
        try:
            version = pkg_resources.get_distribution(package).version
            print(f"✓ {package} {version}")
        except pkg_resources.DistributionNotFound:
            print(f"❌ {package} not installed")
            all_installed = False
    
    return all_installed


def check_directory_structure():
    """Check required directories exist"""
    required_dirs = [
        'hipaa_training',
        'content',
        'tests',
        'scripts'
    ]
    
    all_exist = True
    
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✓ {directory}/ exists")
        else:
            print(f"❌ {directory}/ missing")
            all_exist = False
    
    return all_exist


def check_content_files():
    """Check content files exist and are valid JSON"""
    content_files = [
        'content/lessons.json',
        'content/quiz_questions.json',
        'content/checklist_items.json'
    ]
    
    all_valid = True
    
    for filepath in content_files:
        if not Path(filepath).exists():
            print(f"⚠️  {filepath} missing (will be auto-created)")
            continue
        
        try:
            import json
            with open(filepath, 'r') as f:
                json.load(f)
            print(f"✓ {filepath} valid")
        except json.JSONDecodeError as e:
            print(f"❌ {filepath} invalid JSON: {e}")
            all_valid = False
    
    return all_valid


def main():
    """Run all environment checks"""
    print("🔍 Environment Validation")
    print("=" * 50)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Environment Variables", check_environment_variables),
        ("Dependencies", check_dependencies),
        ("Directory Structure", check_directory_structure),
        ("Content Files", check_content_files)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        print("-" * 50)
        results.append(check_func())
    
    print("\n" + "=" * 50)
    
    if all(results):
        print("✅ All environment checks passed!")
        return 0
    else:
        print("❌ Some environment checks failed")
        print("\nTo fix:")
        print("1. Generate keys: python -c 'import secrets; print(secrets.token_urlsafe(32))'")
        print("2. Set environment: export HIPAA_ENCRYPTION_KEY='<generated-key>'")
        print("3. Install packages: pip install -r requirements.txt")
        return 1


if __name__ == '__main__':
    sys.exit(main())

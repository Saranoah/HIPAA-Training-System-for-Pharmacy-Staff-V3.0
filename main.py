#!/usr/bin/env python3
"""
HIPAA Training System V3.0 - Main Entry Point

A production-ready training application for pharmacy staff to complete
HIPAA compliance training with secure authentication, lessons, adaptive
quizzes, checklists, and automatic certificate generation.

Author: Israa Ali
GitHub: https://github.com/Saranoah/HIPAA-Training-System-for-Pharmacy-Staff-V3.0
License: MIT
"""

import os
import sys
import platform
import argparse

def setup_production_environment():
    """
    Setup production directories and secure permissions

    FIXES APPLIED:
    - Cross-platform permission handling
    - Better error handling
    - Directory structure validation
    """
    required_dirs = [
        "content",
        "reports",
        "certificates",
        "evidence",
        "data",
        "logs"
    ]
    # Create all required directories
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}/")
    # Set secure permissions (Unix/Linux/macOS only)
    if platform.system() != 'Windows':
        for directory in required_dirs:
            try:
                os.chmod(directory, 0o700)  # rwx------
                print(f"✓ Secured permissions: {directory}/")
            except Exception as e:
                print(f"⚠ Warning: Could not set permissions on {directory}/: {e}")
    else:
        print("ℹ Running on Windows - skipping Unix permission settings")
    # Initialize database
    try:
        from hipaa_training.models import DatabaseManager
        DatabaseManager()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)
    print("\n✅ Production environment setup complete!\n")

def check_environment():
    """
    Verify required environment variables are set

    NEW: Added environment validation
    """
    required_vars = ['HIPAA_ENCRYPTION_KEY']
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    if missing_vars:
        print("❌ CRITICAL: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nTo generate a secure encryption key, run:")
        print("   python -c 'import secrets; print(secrets.token_urlsafe(32))'")
        print("\nThen set it in your environment:")
        print("   export HIPAA_ENCRYPTION_KEY='<your-generated-key>'")
        print("   # or on Windows:")
        print("   set HIPAA_ENCRYPTION_KEY=<your-generated-key>")
        sys.exit(1)

def display_system_info():
    """Display system information for debugging"""
    print("=" * 60)
    print("HIPAA Training System V3.0")
    print("=" * 60)
    print(f"Python Version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Working Directory: {os.getcwd()}")
    print("=" * 60 + "\n")

def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="HIPAA Training System V3.0 for Pharmacy Staff",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start interactive training
  python main.py --version          # Show version info
  python main.py --setup-only       # Setup environment only
  python main.py --check-env        # Check environment variables
        """
    )
    parser.add_argument(
        '--version',
        action='version',
        version='HIPAA Training System V3.0.0'
    )
    parser.add_argument(
        '--setup-only',
        action='store_true',
        help='Setup production environment and exit'
    )
    parser.add_argument(
        '--check-env',
        action='store_true',
        help='Check environment variables and exit'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with verbose output'
    )
    args = parser.parse_args()
    # Display system info in debug mode
    if args.debug:
        display_system_info()
    # Check environment variables
    if args.check_env:
        print("Checking environment configuration...")
        check_environment()
        print("✅ All required environment variables are set!")
        return 0
    # Setup environment
    try:
        check_environment()  # Verify env vars first
        setup_production_environment()
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1
    # Exit if setup-only flag is set
    if args.setup_only:
        print("Setup complete. Exiting as requested (--setup-only).")
        return 0
    # Start the application
    try:
        from hipaa_training.cli import CLI
        cli = CLI()
        cli.run()
        return 0
    except KeyboardInterrupt:
        print("\n\n👋 Training session interrupted by user. Goodbye!")
        return 0
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())


if __name__ == "__main__":
    sys.exit(main())

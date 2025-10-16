import os
import sys
import platform
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"✓ Created directory: {dir_path}")

    # Set secure permissions (Unix/Linux/macOS only)
    if platform.system() != 'Windows':
        for directory in required_dirs:
            dir_path = Path(directory)
            try:
                dir_path.chmod(0o700)  # rwx------
                logging.info(f"✓ Secured permissions: {dir_path}")
            except Exception as e:
                logging.warning(f"⚠ Warning: Could not set permissions on {dir_path}: {e}")
    else:
        logging.info("ℹ Running on Windows - skipping Unix permission settings")

    # Initialize database
    try:
        from hipaa_training.models import DatabaseManager
        DatabaseManager()
        logging.info("✓ Database initialized successfully")
    except Exception as e:
        logging.error(f"❌ Failed to initialize database: {e}")
        sys.exit(1)

    logging.info("\n✅ Production environment setup complete!\n")


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
        logging.error("❌ CRITICAL: Missing required environment variables:")
        for var in missing_vars:
            logging.error(f"   - {var}")
        logging.error("\nTo generate a secure encryption key, run:")
        logging.error("   python -c 'import secrets; print(secrets.token_urlsafe(32))'")
        logging.error("\nThen set it in your environment:")
        logging.error("   export HIPAA_ENCRYPTION_KEY='<your-generated-key>'")
        logging.error("   # or on Windows:")
        logging.error("   set HIPAA_ENCRYPTION_KEY=<your-generated-key>")
        sys.exit(1)


def display_system_info():
    """Display system information for debugging"""
    logging.info("="*60)
    logging.info("HIPAA Training System V3.0")
    logging.info("="*60)
    logging.info(f"Python Version: {sys.version}")
    logging.info(f"Platform: {platform.system()} {platform.release()}")
    logging.info(f"Working Directory: {os.getcwd()}")
    logging.info("="*60 + "\n")


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
        '-- '--

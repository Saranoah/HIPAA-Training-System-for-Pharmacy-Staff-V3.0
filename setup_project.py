#!/usr/bin/env python3
"""
Setup Script for HIPAA Training System v4.0.1
"""

from pathlib import Path
import json

def setup_project():
    """Set up project directories and initial files."""
    print("🚀 Setting up HIPAA Training System...")
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    print("✅ Setup complete - ready for PythonAnywhere!")
    print("💡 Run: python main.py")

if __name__ == "__main__":
    setup_project()

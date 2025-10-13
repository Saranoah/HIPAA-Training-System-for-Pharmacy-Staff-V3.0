#!/bin/bash
# HIPAA Training System V3.0 - Production Setup Script

set -e  # Exit on error

echo "🏥 HIPAA Training System V3.0 - Production Setup"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root (not recommended)
if [[ $EUID -eq 0 ]]; then
   echo -e "${YELLOW}⚠️  Warning: Running as root is not recommended${NC}"
   read -p "Continue anyway? (y/n) " -n 1 -r
   echo
   if [[ ! $REPLY =~ ^[Yy]$ ]]; then
       exit 1
   fi
fi

# Check Python version
echo "🐍 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓ Python version: $python_version${NC}"

# Check if Python version is sufficient
if [[ $(echo "$python_version < 3.9" | bc -l 2>/dev/null || echo "1") -eq 1 ]]; then
    echo -e "${YELLOW}⚠️  Python 3.9+ recommended. You have $python_version${NC}"
fi

# Create necessary directories
echo ""
echo "📁 Creating directory structure..."
mkdir -p content reports certificates evidence backups data logs
echo -e "${GREEN}✓ Directories created${NC}"

# Check if content files exist
echo ""
echo "📚 Checking content files..."
if [[ ! -f "content/lessons.json" ]]; then
    echo -e "${YELLOW}⚠️  content/lessons.json not found - will be created on first run${NC}"
fi
if [[ ! -f "content/quiz_questions.json" ]]; then
    echo -e "${YELLOW}⚠️  content/quiz_questions.json not found - will be created on first run${NC}"
fi
if [[ ! -f "content/checklist_items.json" ]]; then
    echo -e "${YELLOW}⚠️  content/checklist_items.json not found - will be created on first run${NC}"
fi

# Check if requirements.txt exists
if [[ ! -f "requirements.txt" ]]; then
    echo -e "${RED}❌ requirements.txt not found!${NC}"
    exit 1
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install --upgrade pip
pip3 install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check for .env file
echo ""
if [[ ! -f ".env" ]]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    
    if [[ -f ".env.example" ]]; then
        echo "📝 Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created${NC}"
    fi
fi

# Generate encryption key if not set
if [[ -z "$HIPAA_ENCRYPTION_KEY" ]] && ! grep -q "HIPAA_ENCRYPTION_KEY=" .env 2>/dev/null; then
    echo ""
    echo "🔑 Generating encryption key..."
    GENERATED_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "HIPAA_ENCRYPTION_KEY=\"$GENERATED_KEY\"" >> .env
    echo -e "${GREEN}✓ Encryption key generated and saved to .env${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANT: Keep .env file secure and backed up!${NC}"
fi

# Generate random salt if not set
if [[ -z "$HIPAA_SALT" ]] && ! grep -q "HIPAA_SALT=" .env 2>/dev/null; then
    echo "🧂 Generating salt..."
    GENERATED_SALT=$(python3 -c "import secrets; print(secrets.token_hex(16))")
    echo "HIPAA_SALT=\"$GENERATED_SALT\"" >> .env
    echo -e "${GREEN}✓ Salt generated and saved to .env${NC}"
fi

# Set secure permissions (Unix-like systems only)
echo ""
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" ]]; then
    echo "🔒 Setting secure file permissions..."
    chmod 700 certificates reports evidence data logs backups 2>/dev/null || true
    chmod 600 .env 2>/dev/null || true
    echo -e "${GREEN}✓ Permissions set${NC}"
else
    echo -e "${YELLOW}ℹ️  Skipping permission settings on Windows${NC}"
fi

# Initialize database
echo ""
echo "🗄️  Initializing database..."
python3 << 'EOF'
import sys
import os

# Load .env file
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"')

try:
    from hipaa_training.models import DatabaseManager
    db = DatabaseManager()
    print('✓ Database initialized successfully')
    sys.exit(0)
except Exception as e:
    print(f'✗ Database initialization failed: {e}')
    sys.exit(1)
EOF

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✓ Database ready${NC}"
else
    echo -e "${RED}❌ Database initialization failed${NC}"
    exit 1
fi

# Run health check
echo ""
echo "🏥 Running health check..."
python3 scripts/health_check.py

echo ""
echo "================================================"
echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Review .env file and ensure encryption key is secure"
echo "2. Review content/ files for your organization"
echo "3. Run: python3 main.py"
echo "4. Create admin users and start training"
echo ""
echo "For production deployment:"
echo "- Backup .env file securely"
echo "- Configure regular backups: scripts/backup_database.sh"
echo "- Monitor audit logs: logs/hipaa_audit.log"
echo "- Set up log rotation and monitoring"
echo ""
echo "📚 Documentation: README.md"
echo "🔧 Troubleshooting: docs/TROUBLESHOOTING.md"

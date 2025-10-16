#!/bin/bash
# HIPAA Training System - Database Backup Script

set -e  # Exit on error

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_PATH="data/hipaa_training.db"

echo "💾 Starting HIPAA Training System backup..."
echo "Timestamp: $TIMESTAMP"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup SQLite database
if [[ -f "$DB_PATH" ]]; then
    echo "📊 Backing up SQLite database..."
    
    # Check if sqlite3 is available
    if command -v sqlite3 &> /dev/null; then
        sqlite3 "$DB_PATH" ".backup $BACKUP_DIR/hipaa_training_$TIMESTAMP.db"
        
        # Compress backup
        if command -v gzip &> /dev/null; then
            gzip "$BACKUP_DIR/hipaa_training_$TIMESTAMP.db"
            echo "✅ Database backed up: $BACKUP_DIR/hipaa_training_$TIMESTAMP.db.gz"
        else
            echo "⚠️  gzip not found - backup saved uncompressed"
        fi
    else
        echo "⚠️  sqlite3 command not found - using simple copy"
        cp "$DB_PATH" "$BACKUP_DIR/hipaa_training_$TIMESTAMP.db"
    fi
else
    echo "⚠️  Database file $DB_PATH not found - skipping database backup"
fi

# Backup content files
if [[ -d "content" ]]; then
    echo "📝 Backing up content files..."
    tar -czf "$BACKUP_DIR/content_$TIMESTAMP.tar.gz" content/
    echo "✅ Content backed up: $BACKUP_DIR/content_$TIMESTAMP.tar.gz"
fi

# Backup audit logs
if [[ -f "logs/hipaa_audit.log" ]]; then
    echo "📋 Backing up audit logs..."
    cp logs/hipaa_audit.log "$BACKUP_DIR/hipaa_audit_$TIMESTAMP.log"
    gzip "$BACKUP_DIR/hipaa_audit_$TIMESTAMP.log"
    echo "✅ Audit log backed up: $BACKUP_DIR/hipaa_audit_$TIMESTAMP.log.gz"
elif [[ -f "hipaa_audit.log" ]]; then
    # Old location fallback
    cp hipaa_audit.log "$BACKUP_DIR/hipaa_audit_$TIMESTAMP.log"
    gzip "$BACKUP_DIR/hipaa_audit_$TIMESTAMP.log"
fi

# Backup evidence files (encrypted)
if [[ -d "evidence" ]] && [[ ! -z "$(ls -A evidence)" ]]; then
    echo "📁 Backing up evidence files..."
    tar -czf "$BACKUP_DIR/evidence_$TIMESTAMP.tar.gz" evidence/
    echo "✅ Evidence backed up: $BACKUP_DIR/evidence_$TIMESTAMP.tar.gz"
fi

# Clean up old backups (keep last 30 days)
echo "🧹 Cleaning up old backups (>30 days)..."
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null || true

# Calculate total backup size
if command -v du &> /dev/null; then
    BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
    echo "📊 Total backup size: $BACKUP_SIZE"
fi

echo ""
echo "✅ Backup completed successfully!"
echo "📁 Backup location: $BACKUP_DIR/"
echo "📅 Backup timestamp: $TIMESTAMP"
STAMP"

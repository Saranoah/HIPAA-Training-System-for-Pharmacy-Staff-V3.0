#!/usr/bin/env python3
"""
HIPAA Training System CLI - PythonAnywhere Production Edition  
Version: 4.0.1 - All Critical Issues Resolved
Architecture: Zero-dependency, maximum compatibility
"""

import os
import sys
import json
import traceback
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import sys
from cli.cli import main

if __name__ == "__main__":
    sys.exit(main())

# ============================================================================
# CLOUD-OPTIMIZED CONFIGURATION - FIXED: Moved to top
# ============================================================================

@dataclass
class CloudConfig:
    """Cloud-optimized configuration with environment awareness."""
    pass_threshold: int = field(default=80, metadata={"min": 50, "max": 100})
    xp_per_lesson: int = field(default=15)
    xp_per_quiz_question: int = field(default=10)
    xp_per_checklist_item: int = field(default=5)
    data_dir: str = field(default_factory=lambda: os.getenv('HIPAA_DATA_DIR', 'data'))
    debug_mode: bool = field(default_factory=lambda: os.getenv('HIPAA_DEBUG', 'false').lower() == 'true')
    
    def __post_init__(self):
        """Validate configuration on initialization."""
        if not 50 <= self.pass_threshold <= 100:
            raise ValueError("Pass threshold must be between 50-100")
        if self.xp_per_lesson < 0:
            raise ValueError("XP values cannot be negative")

    @classmethod
    def from_environment(cls) -> 'CloudConfig':
        """Create configuration from environment variables with fallbacks."""
        return cls(
            pass_threshold=int(os.getenv('HIPAA_PASS_THRESHOLD', '80')),
            xp_per_lesson=int(os.getenv('HIPAA_XP_PER_LESSON', '15')),
            xp_per_quiz_question=int(os.getenv('HIPAA_XP_PER_QUIZ', '10')),
            xp_per_checklist_item=int(os.getenv('HIPAA_XP_PER_CHECKLIST', '5')),
            data_dir=os.getenv('HIPAA_DATA_DIR', 'data'),
            debug_mode=os.getenv('HIPAA_DEBUG', 'false').lower() == 'true'
        )

# FIXED: CONFIG initialized immediately after class definition
try:
    CONFIG = CloudConfig.from_environment()
except Exception as e:
    print(f"⚠️  Configuration error: {e} - using safe defaults")
    CONFIG = CloudConfig()

class ExitCode(Enum):
    """Standardized exit codes for production monitoring."""
    SUCCESS = 0
    UNKNOWN_ERROR = 1
    CONFIG_ERROR = 2
    DATA_ERROR = 3
    KEYBOARD_INTERRUPT = 130

# ============================================================================
# COMPLETE CONTENT - FIXED: All 13 lessons included
# ============================================================================

COMPLETE_LESSONS = {
    "What is PHI?": {
        "icon": "🏥", "order": 1, "duration": "10 minutes", "xp_value": 15,
        "content": "Protected Health Information (PHI) is any information about health status, healthcare provision, or payment that can identify an individual. HIPAA protects 18 specific identifiers.",
        "key_points": [
            "18 HIPAA Identifiers: Name, address, DOB, SSN, medical record number, phone, email, photos, etc.",
            "Pharmacy PHI Examples: Prescription history, medication lists, insurance info, allergies, patient accounts",
            "De-identified data (no identifiers) is NOT PHI and can be used freely",
            "Even a single identifier linked to health info becomes PHI requiring protection"
        ]
    },
    "Privacy Rule": {
        "icon": "🔒", "order": 2, "duration": "15 minutes", "xp_value": 15,
        "content": "HIPAA Privacy Rule protects patient information and requires minimum necessary use. It establishes national standards for protecting PHI.",
        "key_points": [
            "Patient authorization required for most disclosures",
            "Minimum necessary standard applies to routine uses",
            "Patients have rights to access their own records",
            "Treatment, payment, and operations (TPO) allowed without authorization"
        ]
    },
    "Security Rule": {
        "icon": "🛡️", "order": 3, "duration": "15 minutes", "xp_value": 15,
        "content": "HIPAA Security Rule requires administrative, physical, and technical safeguards for electronic Protected Health Information (ePHI).",
        "key_points": [
            "Encryption of data at rest and in transit",
            "Access controls and user authentication required",
            "Audit trails and monitoring systems mandatory",
            "Risk analysis and management processes must be documented"
        ]
    },
    "Patient Rights": {
        "icon": "⚖️", "order": 4, "duration": "20 minutes", "xp_value": 20,
        "content": "HIPAA grants patients seven fundamental rights regarding their health information. Pharmacies must honor these rights and respond to requests within specific timeframes.",
        "key_points": [
            "Right to Access: View/copy records within 30 days, can charge reasonable copying fee",
            "Right to Amend: Request corrections to errors, pharmacy must respond within 60 days",
            "Right to Accounting: List of disclosures for past 6 years",
            "Right to Request Restrictions: Ask to limit uses/disclosures",
            "Right to Confidential Communications: Request alternate contact methods",
            "Right to Notice of Privacy Practices: Receive written NPP",
            "Right to Complain: File complaints with pharmacy or HHS without retaliation"
        ]
    },
    "Breach Notification": {
        "icon": "⚠️", "order": 5, "duration": "15 minutes", "xp_value": 15,
        "content": "HIPAA requires notifying affected patients and HHS within 60 days if PHI is breached. A breach is unauthorized access, use, or disclosure that compromises security or privacy.",
        "key_points": [
            "60-day notification timeline from discovery of breach",
            "Patient notification required for all breaches",
            "HHS reporting mandatory for breaches affecting 500+ individuals",
            "Media notification required for breaches over 500 people",
            "Document all breach investigations even if no notification needed"
        ]
    },
    "Violations & Penalties": {
        "icon": "⚖️", "order": 6, "duration": "15 minutes", "xp_value": 15,
        "content": "HIPAA violations carry significant financial and criminal penalties. Understanding the consequences helps emphasize why compliance matters for every pharmacy staff member.",
        "key_points": [
            "Civil Penalties: $100 to $50,000 per violation (up to $1.9M per year for repeated violations)",
            "Criminal Penalties: Up to 10 years prison + $250,000 for violations with malicious intent",
            "Real Cases: CVS ($2.25M for improper disposal), Walgreens ($1.4M for dumpster PHI)",
            "Individual Liability: Staff members can be personally fined or prosecuted",
            "Violation Categories: Unknowing, reasonable cause, willful neglect (corrected/uncorrected)"
        ]
    },
    "Business Associates": {
        "icon": "🤝", "order": 7, "duration": "15 minutes", "xp_value": 15,
        "content": "A Business Associate (BA) is any vendor or contractor that accesses PHI on behalf of your pharmacy. HIPAA requires written agreements (BAAs) with all BAs before sharing any PHI.",
        "key_points": [
            "Who is a BA: Billing companies, IT support, shredding services, cloud storage, software vendors",
            "BAA Requirements: Must be signed BEFORE PHI access, defines protection responsibilities",
            "Pharmacy Liability: You're responsible if your BA causes a breach",
            "Common Mistake: Assuming vendors 'know' HIPAA - always get signed BAA first",
            "Regular Reviews: Audit BA compliance annually, update agreements when services change"
        ]
    },
    "Secure Disposal": {
        "icon": "🗑️", "order": 8, "duration": "15 minutes", "xp_value": 15,
        "content": "Improper disposal of PHI is one of the most common HIPAA violations in pharmacies. All PHI must be destroyed in a way that makes it unreadable and irretrievable.",
        "key_points": [
            "Paper Records: Cross-cut shred (not tear), burn, or pulverize",
            "Electronic Records: Overwrite hard drives, physically destroy devices",
            "Pharmacy-Specific: Shred prescription labels, expired Rx records, counseling notes",
            "Never: Throw PHI in regular trash, recycle bins, or accessible dumpsters",
            "Retention Rules: Keep records 7 years (varies by state), then proper disposal required",
            "Document: Use certificates of destruction for large batches"
        ]
    },
    "Access Controls": {
        "icon": "🔐", "order": 9, "duration": "15 minutes", "xp_value": 15,
        "content": "Technical safeguards require strict controls over who can access ePHI systems. Proper password management and access controls are essential security measures.",
        "key_points": [
            "Unique User IDs: Every staff member must have own login - NEVER share passwords",
            "Password Standards: Minimum 8 characters (12+ recommended), change every 90 days",
            "Automatic Logoff: System locks after 15 minutes of inactivity",
            "Role-Based Access: Limit system access based on job duties",
            "Immediate Termination: Disable accounts within 24 hours of employee departure",
            "Monitor Access: Review login logs for suspicious activity"
        ]
    },
    "Privacy Practices Notice": {
        "icon": "📄", "order": 10, "duration": "15 minutes", "xp_value": 15,
        "content": "Every pharmacy must provide a Notice of Privacy Practices (NPP) to patients explaining how their PHI will be used and disclosed. This is a legal requirement, not optional.",
        "key_points": [
            "When to Provide: First service date, must obtain good-faith acknowledgment",
            "Must Include: How PHI is used/disclosed, patient rights, complaint procedures",
            "Posting: Display prominently at pharmacy counter and on website",
            "Updates: Revise when policies change, provide new NPP to affected patients",
            "Acknowledgment: Get patient signature or document good-faith effort",
            "Availability: Keep copies at counter for patients to request anytime"
        ]
    },
    "Training Requirements": {
        "icon": "🎓", "order": 11, "duration": "10 minutes", "xp_value": 15,
        "content": "HIPAA requires all pharmacy workforce members to receive training before accessing PHI, with periodic refreshers. Proper documentation of training is mandatory.",
        "key_points": [
            "Initial Training: Must complete before any PHI access",
            "Annual Refresher: Required every 12 months minimum",
            "Who Needs Training: All staff (full-time, part-time, temporary, volunteers, interns)",
            "Documentation Required: Maintain records for 6 years",
            "New Hire Protocol: Complete training within first week",
            "Ongoing Education: Brief reminders at staff meetings"
        ]
    },
    "Incidental Disclosures": {
        "icon": "👂", "order": 12, "duration": "15 minutes", "xp_value": 15,
        "content": "Incidental disclosures are secondary uses or disclosures that cannot reasonably be prevented. Some are permitted under HIPAA if reasonable safeguards are in place.",
        "key_points": [
            "Permitted: Calling patient names in waiting area, sign-in sheets with limited info",
            "Reasonable Safeguards: Lower voices, private counseling areas, position screens away",
            "NOT Permitted: Discussing patients in public areas (elevators, break rooms, parking lots)",
            "Pharmacy Counter: Be aware of who can overhear conversations",
            "Phone Calls: Step away from counter, verify identity before discussing details",
            "Best Practice: Ask yourself 'Could someone else hear/see this?' before speaking"
        ]
    },
    "Patient Request Procedures": {
        "icon": "📋", "order": 13, "duration": "15 minutes", "xp_value": 15,
        "content": "Pharmacies must have documented procedures for responding to patient requests for access, amendments, restrictions, and accountings. Timely responses are required by law.",
        "key_points": [
            "Access Requests: Provide within 30 days, can charge reasonable copy fees",
            "Identity Verification: Always verify government ID + date of birth",
            "Amendment Requests: Review and respond within 60 days",
            "Restriction Requests: Can agree or deny, if agreed must honor consistently",
            "Accounting Requests: Provide list of disclosures for past 6 years",
            "Document Everything: Keep records of all requests and responses"
        ]
    }
}

COMPLETE_QUIZ = [
    {
        "question": "A pharmacy technician accidentally emails a patient's prescription to the wrong email address. What should they do immediately?",
        "options": ["Ignore it and delete the email", "Notify the patient and supervisor immediately", "Report only if the patient complains", "Wait 24 hours to see if there's a response"],
        "correct_index": 1,
        "explanation": "Immediate notification allows for proper breach documentation and mitigation. This is a potential PHI breach requiring immediate action under the Breach Notification Rule."
    },
    {
        "question": "You notice a coworker looking at patient records without a work-related purpose. What action should you take?",
        "options": ["Ignore it - it's not your business", "Report to privacy officer immediately", "Confront them privately first", "Document it but don't report"],
        "correct_index": 1,
        "explanation": "Unauthorized access must be reported to the privacy officer immediately to maintain compliance and patient trust. This is a serious HIPAA violation that could result in penalties for both the individual and pharmacy."
    },
    {
        "question": "A patient requests a copy of their entire prescription history. Under the minimum necessary standard, you should:",
        "options": ["Provide everything without question - it's their information", "Provide only the last 3 months of prescriptions", "Refuse the request entirely", "Ask them to get permission from their doctor first"],
        "correct_index": 0,
        "explanation": "Patients have the right to access their complete health records, including all prescription history. The minimum necessary standard does NOT apply to patient access requests - they can request and receive all their information."
    },
    {
        "question": "A patient's family member calls asking about their medication. The patient is present at home and able to communicate. What should you do?",
        "options": ["Provide the information since family members are allowed access", "Ask to speak with the patient directly first to verify consent", "Refuse to provide any information over the phone", "Ask the family member for the patient's social security number"],
        "correct_index": 1,
        "explanation": "You should verify the patient's consent before sharing information with anyone. Speaking directly with the patient ensures proper authorization. Never assume family members have automatic access to PHI."
    },
    {
        "question": "You discover that ePHI has been stored on an unencrypted laptop that was stolen from your pharmacy. What is the FIRST step?",
        "options": ["Wait to see if the laptop is recovered", "Notify your supervisor and privacy officer immediately", "Change all system passwords", "File a police report only"],
        "correct_index": 1,
        "explanation": "Immediate notification to your supervisor and privacy officer is critical. This is a breach that requires prompt risk assessment and potentially notification to affected individuals within 60 days."
    },
    {
        "question": "Which of the following is considered Protected Health Information (PHI)?",
        "options": ["Patient's favorite color mentioned in casual conversation", "Patient's name alone without any health information", "Patient's prescription medication list", "The weather outside the pharmacy"],
        "correct_index": 2,
        "explanation": "A prescription medication list is PHI because it relates to healthcare and can identify an individual. Name alone without health context is not PHI. The 18 HIPAA identifiers must be linked to health information to be considered PHI."
    },
    {
        "question": "A patient requests to see their prescription records. You must provide access within how many days?",
        "options": ["15 days", "30 days", "60 days", "90 days"],
        "correct_index": 1,
        "explanation": "HIPAA requires covered entities to provide access to records within 30 days of the request. You can extend once for an additional 30 days with written notice, but the standard is 30 days."
    },
    {
        "question": "Your pharmacy uses a cloud-based software system to manage prescriptions. Before using this service, you must:",
        "options": ["Just start using it - the vendor handles HIPAA compliance", "Get a signed Business Associate Agreement (BAA) from the vendor", "Only use it if the vendor is HIPAA certified", "Train all staff on the new system first"],
        "correct_index": 1,
        "explanation": "Any vendor that accesses PHI on your behalf is a Business Associate and requires a signed BAA BEFORE any PHI is shared. You are liable for breaches caused by your business associates, so proper agreements are critical."
    },
    {
        "question": "How should you dispose of prescription labels and patient paperwork?",
        "options": ["Tear them up and throw in regular trash", "Recycle them with other paper products", "Cross-cut shred or use a professional shredding service", "Store them in a locked cabinet indefinitely"],
        "correct_index": 2,
        "explanation": "All PHI must be shredded using cross-cut shredders (not single-cut) or destroyed by professional services. Improper disposal is one of the most common HIPAA violations. CVS was fined $2.25 million for putting PHI in dumpsters."
    },
    {
        "question": "What is the maximum penalty for a single HIPAA violation with willful neglect that is not corrected?",
        "options": ["$5,000", "$25,000", "$50,000", "$1.9 million per year"],
        "correct_index": 3,
        "explanation": "Willful neglect that is not corrected carries a minimum penalty of $50,000 per violation, with an annual maximum of $1.9 million for repeated violations. This is why immediate correction of violations is critical."
    },
    {
        "question": "A coworker asks to use your computer login credentials because they forgot theirs. You should:",
        "options": ["Share your password since you trust them", "Never share - each person must use their unique login", "Share only for emergencies", "Ask your supervisor for permission first"],
        "correct_index": 1,
        "explanation": "Each workforce member must have a unique user ID and NEVER share passwords. Sharing credentials violates HIPAA's access control requirements and makes it impossible to audit who accessed PHI."
    },
    {
        "question": "How often must pharmacy staff complete HIPAA training?",
        "options": ["Only once when first hired", "Every 6 months", "Annually (every 12 months) at minimum", "Only when policies change"],
        "correct_index": 2,
        "explanation": "HIPAA requires workforce training at hire AND periodic refresher training. Annual training is the standard minimum, with additional training required when policies or regulations change."
    },
    {
        "question": "A patient asks you to call their work number instead of home for prescription notifications. This is an example of which patient right?",
        "options": ["Right to access their records", "Right to request confidential communications", "Right to amend their information", "Right to restrict uses of their information"],
        "correct_index": 1,
        "explanation": "The right to request confidential communications allows patients to specify how and where they want to be contacted. Pharmacies must accommodate reasonable requests without asking why."
    },
    {
        "question": "You're discussing a patient's medication regimen with your pharmacist colleague at the counter. Another patient overhears the conversation. This is:",
        "options": ["A major HIPAA violation requiring breach notification", "An acceptable incidental disclosure if you took reasonable precautions", "Not a HIPAA issue since it was accidental", "Only a violation if the patient complains"],
        "correct_index": 1,
        "explanation": "If you took reasonable safeguards (lowered voices, used professional judgment), this may be a permissible incidental disclosure. However, best practice is to use private counseling areas for sensitive discussions whenever possible."
    },
    {
        "question": "A patient wants to file a complaint about how their PHI was handled. What must you tell them?",
        "options": ["They can only complain to the pharmacy manager", "They have the right to file a complaint with HHS without retaliation", "They must wait 30 days before filing a complaint", "Complaints are only accepted in writing"],
        "correct_index": 1,
        "explanation": "Patients have the right to file complaints with the covered entity or directly with the HHS Office for Civil Rights. Retaliation against patients who file complaints is strictly prohibited and can result in additional penalties."
    }
]

COMPLETE_CHECKLIST = [
    {"id": "privacy_training", "text": "Completed Privacy Rule training", "category": "Training"},
    {"id": "security_review", "text": "Reviewed Security Rule requirements", "category": "Training"},
    {"id": "breach_timeline", "text": "Understands breach notification timeline (60 days)", "category": "Knowledge"},
    {"id": "unauthorized_access", "text": "Can identify and report unauthorized access", "category": "Knowledge"},
    {"id": "minimum_necessary", "text": "Knows and applies minimum necessary standard", "category": "Knowledge"},
    {"id": "phi_identification", "text": "Can identify all 18 types of Protected Health Information (PHI)", "category": "Knowledge"},
    {"id": "patient_rights", "text": "Understands all 7 patient rights under HIPAA", "category": "Knowledge"},
    {"id": "ephi_rest", "text": "ePHI encrypted at rest (hard drives, servers)", "category": "Technical"},
    {"id": "ephi_transit", "text": "ePHI encrypted in transit (secure transmissions)", "category": "Technical"},
    {"id": "audit_logs", "text": "Audit logs enabled and monitored regularly", "category": "Technical"},
    {"id": "proper_disposal", "text": "Cross-cut shredders available and used for all PHI disposal", "category": "Technical"},
    {"id": "unique_logins", "text": "Every staff member has unique login credentials (no sharing)", "category": "Technical"},
    {"id": "staff_training", "text": "All staff HIPAA training completed annually", "category": "Compliance"},
    {"id": "baa_signed", "text": "Business Associate Agreements signed with all vendors", "category": "Compliance"},
    {"id": "npp_provided", "text": "Notice of Privacy Practices provided to all patients and posted prominently", "category": "Compliance"}
]

# ============================================================================
# CLOUD-SAFE DEPENDENCY MANAGEMENT - FIXED: Uses CONFIG now available
# ============================================================================

class RichManager:
    """Safe Rich console manager with zero-crash guarantee."""
    
    def __init__(self):
        self.console = None
        self.available = False
        self._initialize_rich()
    
    def _initialize_rich(self) -> None:
        """Initialize Rich with comprehensive error containment."""
        try:
            # Test import safely
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table
            from rich.progress import Progress
            
            self.console = Console()
            self.available = True
            if CONFIG.debug_mode:  # ✅ FIXED: CONFIG now available
                print("✅ Rich UI enhancements enabled")
        except ImportError as e:
            self.available = False
            if CONFIG.debug_mode:  # ✅ FIXED: CONFIG now available
                print(f"🔧 Rich not available: {e} - Using basic mode")
        except Exception as e:
            self.available = False
            if CONFIG.debug_mode:  # ✅ FIXED: CONFIG now available
                print(f"⚠️ Rich initialization failed: {e} - Using basic mode")
    
    def safe_print(self, content: str, style: str = None) -> None:
        """Zero-crash print method."""
        try:
            if self.available and self.console:
                self.console.print(content, style=style)
            else:
                # Strip any Rich markup and print safely
                clean_content = self._strip_rich_markup(str(content))
                print(clean_content)
        except Exception as e:
            # Ultimate fallback
            print(f"PRINT_FALLBACK: {content}")
    
    def safe_panel(self, content: str, title: str = "", border_style: str = "blue") -> None:
        """Zero-crash panel display."""
        try:
            if self.available and self.console:
                from rich.panel import Panel
                panel = Panel(content, title=title, border_style=border_style)
                self.console.print(panel)
            else:
                self._print_basic_panel(content, title)
        except Exception as e:
            self._print_basic_panel(content, title)
    
    def _strip_rich_markup(self, text: str) -> str:
        """Basic Rich markup stripping."""
        # Remove simple style tags (very basic implementation)
        import re
        return re.sub(r'\[.*?\]', '', text)
    
    def _print_basic_panel(self, content: str, title: str) -> None:
        """Fallback panel display."""
        width = 60
        print(f"\n{'=' * width}")
        if title:
            print(f" {title} ".center(width, ' '))
            print(f"{'-' * width}")
        print(content)
        print(f"{'=' * width}")

# ============================================================================
# CLOUD DATA MANAGEMENT - PYTHONANYWHERE OPTIMIZED
# ============================================================================

class CloudDataManager:
    """PythonAnywhere-optimized data management with atomic safety."""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.data_dir = Path(config.data_dir)
        self.progress_file = self.data_dir / "user_progress.json"
        self.audit_file = self.data_dir / "audit_log.jsonl"
        self.backup_dir = self.data_dir / "backups"
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist safely."""
        try:
            self.data_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
            self.backup_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠️  Directory creation failed: {e}")
            # Continue anyway - some operations might still work
    
    def get_progress_path(self) -> Path:
        """Get validated progress file path."""
        return self.progress_file
    
    def get_audit_path(self) -> Path:
        """Get validated audit file path."""
        return self.audit_file
    
    def create_backup(self, source_path: Path) -> bool:
        """Create timestamped backup of a file."""
        try:
            if not source_path.exists():
                return True  # Nothing to backup
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(source_path, backup_path)
            if CONFIG.debug_mode:
                print(f"✅ Backup created: {backup_path}")
            return True
        except Exception as e:
            if CONFIG.debug_mode:
                print(f"⚠️  Backup failed: {e}")
            return False

# ============================================================================
# ATOMIC FILE OPERATIONS - PRODUCTION GRADE
# ============================================================================

class AtomicFileManager:
    """Production-grade atomic file operations."""
    
    @staticmethod
    def atomic_json_write(data: Any, filepath: Path) -> bool:
        """
        Atomic JSON write with temp file and atomic move.
        
        Returns:
            bool: True if successful, False otherwise
        """
        temp_path = None
        try:
            # Ensure directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Create temp file in same directory for atomic move
            with tempfile.NamedTemporaryFile(
                mode='w', 
                encoding='utf-8',
                delete=False,
                dir=filepath.parent,
                suffix='.tmp'
            ) as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                temp_path = Path(f.name)
            
            # Atomic replace
            shutil.move(str(temp_path), str(filepath))
            return True
            
        except Exception as e:
            print(f"❌ Atomic write failed: {e}")
            # Cleanup temp file
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            return False
    
    @staticmethod
    def atomic_json_read(filepath: Path, default: Any = None) -> Any:
        """
        Atomic JSON read with corruption recovery.
        
        Returns:
            Parsed data or default if unrecoverable
        """
        if default is None:
            default = {}
            
        if not filepath.exists():
            return default
        
        try:
            # Primary read attempt
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"⚠️  File corrupted, attempting recovery: {e}")
            
            # Recovery: create backup and return default
            backup_mgr = CloudDataManager(CONFIG)
            backup_mgr.create_backup(filepath)
            
            # Try to read as text for partial recovery (advanced)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"📄 Corrupted content (first 200 chars): {content[:200]}...")
            except:
                pass
                
            print("🔄 Restoring from defaults")
            return default
            
        except Exception as e:
            print(f"❌ File read failed: {e}")
            return default
    
    @staticmethod
    def atomic_append_line(data: str, filepath: Path) -> bool:
        """Atomic line append with flush guarantee."""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'a', encoding='utf-8', buffering=1) as f:
                f.write(data + '\n')
                f.flush()  # Force write to disk
            return True
        except Exception as e:
            print(f"❌ Append failed: {e}")
            return False

# ============================================================================
# PRODUCTION PROGRESS MANAGEMENT
# ============================================================================

class ProgressManager:
    """Enterprise-grade progress management with atomic safety."""
    
    def __init__(self, data_manager: CloudDataManager):
        self.data_manager = data_manager
        self.progress_file = data_manager.get_progress_path()
    
    def create_default_progress(self) -> Dict[str, Any]:
        """Create validated default progress structure."""
        return {
            "version": "4.0.1",
            "xp": 0,
            "level": 1,
            "lessons_completed": [],
            "quiz_scores": [],
            "checklist": {item["id"]: False for item in COMPLETE_CHECKLIST},
            "last_login": datetime.now().isoformat(),
            "total_time": 0,
            "badges": [],
            "created_at": datetime.now().isoformat(),
            "environment": "pythonanywhere"
        }
    
    def deep_merge_progress(self, default: Dict, user: Dict) -> Dict:
        """Safely merge user progress with defaults, preserving structure."""
        result = default.copy()
        
        for key, value in user.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self.deep_merge_progress(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    # For lists, we want to preserve the user's data but ensure type safety
                    result[key] = value
                else:
                    # Type-safe assignment
                    if type(value) == type(result[key]):
                        result[key] = value
                    else:
                        print(f"⚠️  Type mismatch for {key}, using default")
            else:
                result[key] = value
        
        return result
    
    def load_progress(self) -> Dict[str, Any]:
        """Load user progress with comprehensive error recovery."""
        default_progress = self.create_default_progress()
        
        try:
            if self.progress_file.exists():
                # Create backup before any read attempt
                self.data_manager.create_backup(self.progress_file)
                
                # Atomic read with recovery
                user_data = AtomicFileManager.atomic_json_read(self.progress_file, default_progress)
                
                if user_data and isinstance(user_data, dict):
                    merged_progress = self.deep_merge_progress(default_progress, user_data)
                    
                    # Validate critical structure
                    if "checklist" not in merged_progress:
                        merged_progress["checklist"] = default_progress["checklist"]
                    
                    if CONFIG.debug_mode:
                        print(f"✅ Progress loaded: {len(merged_progress.get('lessons_completed', []))} lessons completed")
                    
                    return merged_progress
                else:
                    print("⚠️  Progress file invalid - using defaults")
            else:
                if CONFIG.debug_mode:
                    print("🔍 No progress file found - using defaults")
                    
        except Exception as e:
            print(f"❌ Progress load failed: {e}")
            if CONFIG.debug_mode:
                traceback.print_exc()
        
        return default_progress
    
    def save_progress(self, progress: Dict[str, Any]) -> bool:
        """Save progress with atomic safety and backup."""
        try:
            # Update metadata
            progress["last_updated"] = datetime.now().isoformat()
            progress["version"] = "4.0.1"
            
            # Atomic save
            success = AtomicFileManager.atomic_json_write(progress, self.progress_file)
            
            if success and CONFIG.debug_mode:
                print(f"✅ Progress saved: {progress['xp']} XP, Level {progress['level']}")
            
            return success
            
        except Exception as e:
            print(f"❌ Progress save failed: {e}")
            if CONFIG.debug_mode:
                traceback.print_exc()
            return False

# ============================================================================
# PRODUCTION AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """HIPAA-compliant audit logging."""
    
    def __init__(self, data_manager: CloudDataManager):
        self.data_manager = data_manager
        self.audit_file = data_manager.get_audit_path()
    
    def log_event(self, event_type: str, details: Dict[str, Any]) -> bool:
        """Log audit event with atomic safety."""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "details": details,
                "environment": "pythonanywhere"
            }
            
            success = AtomicFileManager.atomic_append_line(
                json.dumps(event, ensure_ascii=False),
                self.audit_file
            )
            
            if success and CONFIG.debug_mode:
                print(f"📊 Audit logged: {event_type}")
            
            return success
            
        except Exception as e:
            print(f"❌ Audit log failed: {e}")
            # Fallback to console in debug mode
            if CONFIG.debug_mode:
                print(f"AUDIT_FALLBACK: {event_type} - {details}")
            return False

# ============================================================================
# PYTHONANYWHERE CLI - PRODUCTION READY
# ============================================================================

class PythonAnywhereCLI:
    """PythonAnywhere-optimized CLI with zero-crash guarantee."""
    
    def __init__(self):
        """Initialize with comprehensive safety checks."""
        self.config = CONFIG  # ✅ FIXED: CONFIG available
        self.data_manager = CloudDataManager(self.config)
        self.progress_manager = ProgressManager(self.data_manager)
        self.audit_logger = AuditLogger(self.data_manager)
        self.rich = RichManager()
        
        # Load progress
        self.progress = self.progress_manager.load_progress()
        
        # Content
        self.lessons = COMPLETE_LESSONS
        self.quiz = COMPLETE_QUIZ
        self.checklist = COMPLETE_CHECKLIST
        
        # Audit startup
        self.audit_logger.log_event("session_start", {
            "mode": "production",
            "rich_available": self.rich.available,
            "user_xp": self.progress.get("xp", 0),
            "environment": "pythonanywhere"
        })
        
        if self.config.debug_mode:
            print("🚀 CLI Initialized Successfully")
    
    def calculate_level(self, xp: int) -> int:
        """Calculate user level based on XP."""
        return max(1, (xp // 100) + 1)
    
    def safe_input(self, prompt: str) -> str:
        """Safe input with keyboard interrupt handling."""
        try:
            return input(prompt).strip()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"❌ Input error: {e}")
            return ""
    
    def validate_quiz_input(self, input_str: Optional[str], max_options: int) -> int:
        """✅ FIXED: Production-grade quiz input validation."""
        if not input_str:
            raise ValueError("Please enter an answer")
        
        try:
            answer_num = int(input_str.strip())
        except ValueError:
            raise ValueError("Please enter a valid number")
        
        if not (1 <= answer_num <= max_options):
            raise ValueError(f"Please enter a number between 1 and {max_options}")
        
        return answer_num - 1  # Convert to 0-based index
    
    def run(self) -> None:
        """Main CLI loop with comprehensive error containment."""
        self.show_welcome()
        
        while True:
            try:
                choice = self.show_main_menu()
                
                if choice == '1':
                    self.show_lessons()
                elif choice == '2':
                    self.take_quiz()
                elif choice == '3':
                    self.show_checklist()
                elif choice == '4':
                    self.show_progress()
                elif choice == '5':
                    self.safe_exit()
                    break
                else:
                    self.rich.safe_print("❌ Invalid choice. Please try again.", "red")
                    
            except KeyboardInterrupt:
                self.rich.safe_print("\n👋 Training session interrupted.", "yellow")
                self.safe_exit()
                break
            except Exception as e:
                self.rich.safe_print(f"❌ Unexpected error: {e}", "red")
                if self.config.debug_mode:
                    traceback.print_exc()
                # Continue running despite errors
    
    def show_welcome(self) -> None:
        """Display cloud-optimized welcome message."""
        welcome_text = f"""
🏥 HIPAA TRAINING SYSTEM - PythonAnywhere Production

📊 Your Progress:
  • Level: {self.progress.get('level', 1)}
  • XP: {self.progress.get('xp', 0)}
  • Lessons Completed: {len(self.progress.get('lessons_completed', []))}/{len(self.lessons)}
  • Checklist Items: {sum(1 for v in self.progress.get('checklist', {}).values() if v)}/{len(self.checklist)}

🌐 Environment: PythonAnywhere Optimized
💡 Use menu options below to continue your training.
        """
        
        self.rich.safe_panel(welcome_text, "Welcome to HIPAA Training", "cyan")
    
    def show_main_menu(self) -> str:
        """Display main menu and get validated user choice."""
        lessons_completed = len(self.progress.get('lessons_completed', []))
        checklist_completed = sum(1 for v in self.progress.get('checklist', {}).values() if v)
        quiz_attempts = len(self.progress.get('quiz_scores', []))
        
        if self.rich.available:
            from rich.table import Table
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Option", style="white", width=8)
            table.add_column("Description", style="green")
            table.add_column("Progress", style="yellow")
            
            table.add_row("1", "📚 View Training Lessons", f"{lessons_completed}/{len(self.lessons)}")
            table.add_row("2", "🎯 Take Compliance Quiz", f"{quiz_attempts} attempts")
            table.add_row("3", "✅ Complete Checklist", f"{checklist_completed}/{len(self.checklist)}")
            table.add_row("4", "📊 View Progress & Stats", "Details")
            table.add_row("5", "🚪 Exit System", "Safe exit")
            
            self.rich.console.print("\n")
            self.rich.console.print(table)
        else:
            print("\n" + "="*60)
            print("📚 MAIN MENU")
            print("="*60)
            print(f"1. View Training Lessons ({lessons_completed}/{len(self.lessons)} completed)")
            print(f"2. Take Compliance Quiz ({quiz_attempts} attempts)")
            print(f"3. Complete Checklist ({checklist_completed}/{len(self.checklist)} items)")
            print("4. View Progress & Statistics")
            print("5. Exit System")
            print("="*60)
        
        while True:
            choice = self.safe_input("\n👉 Enter your choice (1-5): ")
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            self.rich.safe_print("❌ Please enter a number between 1-5", "red")
    
    def show_lessons(self) -> None:
        """Display and manage training lessons."""
        self.rich.safe_panel("Browse and complete all HIPAA training lessons", "📚 Training Lessons", "blue")
        
        lesson_titles = list(self.lessons.keys())
        
        for idx, title in enumerate(lesson_titles, 1):
            lesson = self.lessons[title]
            completed = title in self.progress.get("lessons_completed", [])
            status_icon = "✅" if completed else "📖"
            
            self.rich.safe_print(
                f"{status_icon} {idx}. {lesson['icon']} {title} "
                f"({lesson.get('duration', 'N/A')})",
                "green" if completed else "white"
            )
        
        while True:
            try:
                choice = self.safe_input("\n👉 Select lesson (1-{}) or 0 to return: ".format(len(lesson_titles)))
                if choice == '0':
                    return
                
                lesson_idx = int(choice) - 1
                if 0 <= lesson_idx < len(lesson_titles):
                    self.display_lesson(lesson_titles[lesson_idx])
                    break
                else:
                    self.rich.safe_print(f"❌ Please enter a number between 1-{len(lesson_titles)}", "red")
            except ValueError:
                self.rich.safe_print("❌ Please enter a valid number", "red")
    
    def display_lesson(self, title: str) -> None:
        """Display a specific lesson with safe formatting."""
        lesson = self.lessons[title]
        
        # Display lesson content safely
        content = f"{title}\n\n{lesson['content']}"
        self.rich.safe_panel(content, f"{lesson['icon']} Lesson", "blue")
        
        # Display key points
        self.rich.safe_print("\n🔑 Key Points:", "bold")
        for point in lesson["key_points"]:
            self.rich.safe_print(f"  • {point}")
        
        self.safe_input("\n📚 Press Enter when you've finished reading...")
        
        # Mark as completed and award XP
        if title not in self.progress.get("lessons_completed", []):
            self.progress.setdefault("lessons_completed", []).append(title)
            xp_earned = lesson.get("xp_value", self.config.xp_per_lesson)
            self.progress["xp"] = self.progress.get("xp", 0) + xp_earned
            self.progress["level"] = self.calculate_level(self.progress["xp"])
            
            if self.progress_manager.save_progress(self.progress):
                completion_msg = f"🎉 Lesson completed! +{xp_earned} XP (Level {self.progress['level']})"
                self.rich.safe_print(completion_msg, "green")
                
                self.audit_logger.log_event("lesson_completed", {
                    "lesson": title,
                    "xp_earned": xp_earned,
                    "new_level": self.progress["level"]
                })
            else:
                self.rich.safe_print("⚠️  Progress saved locally but may not persist", "yellow")
    
    def take_quiz(self) -> None:
        """Administer quiz with comprehensive input validation."""
        quiz_info = f"""
🎯 HIPAA COMPLIANCE QUIZ

• Questions: {len(self.quiz)}
• Passing Score: {self.config.pass_threshold}% 
• XP: {self.config.xp_per_quiz_question} per correct answer
• Time: Approximately 20-30 minutes

This quiz covers all aspects of HIPAA compliance for pharmacy staff.
        """
        
        self.rich.safe_panel(quiz_info, "Quiz Information", "cyan")
        self.safe_input("Press Enter to begin...")
        
        correct_answers = 0
        question_results = []
        
        for idx, question in enumerate(self.quiz, 1):
            result = self.ask_question(idx, question)
            if result["correct"]:
                correct_answers += 1
            question_results.append(result)
        
        self.show_quiz_results(correct_answers, question_results)
    
    def ask_question(self, question_num: int, question: Dict) -> Dict:
        """Ask a single quiz question with validated input."""
        self.rich.safe_print(f"\nQuestion {question_num} of {len(self.quiz)}", "cyan")
        self.rich.safe_print(f"{question['question']}\n", "bold")
        
        # Display options
        for opt_idx, option in enumerate(question['options'], 1):
            self.rich.safe_print(f"  {opt_idx}. {option}")
        
        # ✅ FIXED: Use dynamic option count instead of hardcoded 4
        max_options = len(question['options'])
        
        # Get and validate answer
        while True:
            try:
                answer_input = self.safe_input(f"\n👉 Your answer (1-{max_options}): ")
                answer_index = self.validate_quiz_input(answer_input, max_options)
                break
            except ValueError as e:
                self.rich.safe_print(f"❌ {e}", "red")
                continue
        
        # Check answer and provide feedback
        is_correct = answer_index == question['correct_index']
        correct_answer_text = question['options'][question['correct_index']]
        
        if is_correct:
            self.rich.safe_print("✅ Correct!", "green")
        else:
            self.rich.safe_print("❌ Incorrect", "red")
            self.rich.safe_print(f"💡 Correct answer: {correct_answer_text}", "yellow")
        
        self.rich.safe_print(f"📚 Explanation: {question['explanation']}", "blue")
        self.safe_input("\nPress Enter to continue...")
        
        return {
            "question_num": question_num,
            "correct": is_correct,
            "user_answer": answer_index,
            "correct_answer": question['correct_index']
        }
    
    def show_quiz_results(self, correct: int, results: List[Dict]) -> None:
        """Display comprehensive quiz results."""
        total_questions = len(self.quiz)
        percentage = (correct / total_questions) * 100
        xp_earned = correct * self.config.xp_per_quiz_question
        
        # Update progress
        self.progress["xp"] = self.progress.get("xp", 0) + xp_earned
        self.progress["level"] = self.calculate_level(self.progress["xp"])
        
        self.progress.setdefault("quiz_scores", []).append({
            "date": datetime.now().isoformat(),
            "score": correct,
            "total": total_questions,
            "percentage": percentage,
            "passed": percentage >= self.config.pass_threshold
        })
        
        if self.progress_manager.save_progress(self.progress):
            # Display results
            results_text = f"""
📊 Quiz Results:

• Questions Answered: {total_questions}
• Correct Answers: {correct}
• Score: {percentage:.1f}%
• XP Earned: +{xp_earned}
• Total XP: {self.progress["xp"]}
• Current Level: {self.progress["level"]}

{'🎉 Congratulations! You passed!' if percentage >= self.config.pass_threshold else '📚 Please review the material and try again!'}
            """
            
            self.rich.safe_panel(
                results_text, 
                "Quiz Complete", 
                "green" if percentage >= self.config.pass_threshold else "yellow"
            )
            
            self.audit_logger.log_event("quiz_completed", {
                "score": percentage,
                "correct": correct,
                "total": total_questions,
                "xp_earned": xp_earned,
                "passed": percentage >= self.config.pass_threshold
            })
        else:
            self.rich.safe_print("⚠️  Results recorded locally but may not persist", "yellow")
        
        self.safe_input("\nPress Enter to continue...")
    
    def show_checklist(self) -> None:
        """Display and manage compliance checklist safely."""
        self.rich.safe_panel(
            f"Complete all compliance checklist items\n"
            f"💎 {self.config.xp_per_checklist_item} XP per completed item\n" 
            f"✅ {len(self.checklist) - 3}/{len(self.checklist)} required for compliance",
            "✅ HIPAA Compliance Checklist", "green"
        )
        
        completed_count = 0
        
        # Display checklist items safely
        for idx, item in enumerate(self.checklist, 1):
            completed = self.progress["checklist"].get(item["id"], False)
            status_icon = "✅" if completed else "❌"
            
            if completed:
                completed_count += 1
            
            self.rich.safe_print(
                f"{status_icon} {idx}. {item['text']} "
                f"({item['category']})",
                "green" if completed else "white"
            )
        
        # Show completion statistics
        completion_percent = (completed_count / len(self.checklist)) * 100
        self.rich.safe_print(f"\n📊 Completion: {completed_count}/{len(self.checklist)} ({completion_percent:.1f}%)", "cyan")
        
        # Toggle items with validation
        while True:
            try:
                choice = self.safe_input(f"\n👉 Toggle item (1-{len(self.checklist)}) or 0 to return: ")
                if choice == '0':
                    break
                
                item_idx = int(choice) - 1
                if 0 <= item_idx < len(self.checklist):
                    item = self.checklist[item_idx]
                    current_state = self.progress["checklist"].get(item["id"], False)
                    new_state = not current_state
                    
                    self.progress["checklist"][item["id"]] = new_state
                    
                    # Award XP for newly completed items
                    if new_state and not current_state:
                        self.progress["xp"] = self.progress.get("xp", 0) + self.config.xp_per_checklist_item
                        self.progress["level"] = self.calculate_level(self.progress["xp"])
                        self.rich.safe_print(f"✅ {item['text']} - Completed! +{self.config.xp_per_checklist_item} XP", "green")
                    elif not new_state and current_state:
                        self.rich.safe_print(f"📝 {item['text']} - Marked incomplete", "yellow")
                    
                    if self.progress_manager.save_progress(self.progress):
                        self.audit_logger.log_event("checklist_updated", {
                            "item": item["id"],
                            "completed": new_state,
                            "total_completed": sum(1 for v in self.progress["checklist"].values() if v)
                        })
                    break
                else:
                    self.rich.safe_print(f"❌ Please enter a number between 1-{len(self.checklist)}", "red")
            except ValueError:
                self.rich.safe_print("❌ Please enter a valid number", "red")
    
    def show_progress(self) -> None:
        """Display comprehensive user progress safely."""
        progress = self.progress
        
        # Calculate statistics
        lessons_completed = len(progress.get('lessons_completed', []))
        total_lessons = len(self.lessons)
        lessons_percent = (lessons_completed / total_lessons) * 100
        
        checklist_completed = sum(1 for v in progress.get('checklist', {}).values() if v)
        total_checklist = len(self.checklist)
        checklist_percent = (checklist_completed / total_checklist) * 100
        
        quiz_attempts = len(progress.get('quiz_scores', []))
        best_quiz_score = max([s['percentage'] for s in progress['quiz_scores']]) if progress.get('quiz_scores') else 0
        
        progress_text = f"""
📊 Progress Overview:

• Level: {progress['level']} ({progress['xp'] % 100}/100 XP to next level)
• Total XP: {progress['xp']}
• Lessons: {lessons_completed}/{total_lessons} ({lessons_percent:.1f}%)
• Checklist: {checklist_completed}/{total_checklist} ({checklist_percent:.1f}%)
• Quiz Attempts: {quiz_attempts}
• Best Quiz Score: {best_quiz_score:.1f}%
• Environment: PythonAnywhere
        """
        
        self.rich.safe_panel(progress_text, "Your Progress", "cyan")
        
        # Show recent quiz history
        if progress.get('quiz_scores'):
            self.rich.safe_print("\n📈 Recent Quiz Scores:", "bold")
            for score in progress['quiz_scores'][-3:]:
                date = datetime.fromisoformat(score['date']).strftime("%m/%d/%Y")
                result = "PASS" if score['percentage'] >= self.config.pass_threshold else "FAIL"
                color = "green" if score['percentage'] >= self.config.pass_threshold else "red"
                self.rich.safe_print(
                    f"  {date}: {score['score']}/{score['total']} ({score['percentage']:.1f}%) - {result}",
                    color
                )
        
        # Overall compliance status
        overall_completion = (lessons_percent + checklist_percent) / 2
        if overall_completion >= 80:
            status_msg = "🎉 Excellent progress! You're on track for compliance."
            status_style = "green"
        elif overall_completion >= 60:
            status_msg = "📚 Good progress! Continue with the remaining items."
            status_style = "yellow"
        else:
            status_msg = "🚨 Keep working! Focus on completing lessons and checklist."
            status_style = "red"
        
        self.rich.safe_print(f"\n{status_msg}", status_style)
        self.safe_input("\nPress Enter to continue...")
    
    def safe_exit(self) -> None:
        """Safe system exit with guaranteed cleanup."""
        self.rich.safe_print("\n👋 Thank you for completing HIPAA training!", "green")
        
        # Final progress save
        self.progress_manager.save_progress(self.progress)
        
        # Audit log
        self.audit_logger.log_event("session_end", {
            "xp": self.progress.get("xp", 0),
            "level": self.progress.get("level", 1),
            "lessons_completed": len(self.progress.get("lessons_completed", [])),
            "checklist_completed": sum(1 for v in self.progress.get("checklist", {}).values() if v),
            "environment": "pythonanywhere"
        })
        
        if self.config.debug_mode:
            print("🔧 Debug: Session ended cleanly")

# ============================================================================
# PYTHONANYWHERE TESTING UTILITIES
# ============================================================================

class PythonAnywhereTester:
    """Comprehensive testing utilities for PythonAnywhere deployment."""
    
    @staticmethod
    def run_production_tests() -> bool:
        """Run comprehensive production readiness tests."""
        print("🧪 RUNNING PYTHONANYWHERE PRODUCTION TESTS")
        print("=" * 60)
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Configuration
        total_tests += 1
        try:
            config = CloudConfig.from_environment()
            print("✅ Configuration test passed")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
        
        # Test 2: Data directory creation
        total_tests += 1
        try:
            data_mgr = CloudDataManager(CONFIG)
            data_mgr._ensure_directories()
            print("✅ Data directory test passed")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Data directory test failed: {e}")
        
        # Test 3: Atomic file operations
        total_tests += 1
        try:
            test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
            test_file = Path("data/test_atomic.json")
            
            # Write
            success = AtomicFileManager.atomic_json_write(test_data, test_file)
            # Read
            read_data = AtomicFileManager.atomic_json_read(test_file)
            # Cleanup
            if test_file.exists():
                test_file.unlink()
                
            if success and read_data["test"] == "data":
                print("✅ Atomic file operations test passed")
                tests_passed += 1
            else:
                print("❌ Atomic file operations test failed")
        except Exception as e:
            print(f"❌ Atomic file operations test failed: {e}")
        
        # Test 4: Rich manager
        total_tests += 1
        try:
            rich_mgr = RichManager()
            rich_mgr.safe_print("✅ Rich manager test passed")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Rich manager test failed: {e}")
        
        # Test 5: Progress management
        total_tests += 1
        try:
            data_mgr = CloudDataManager(CONFIG)
            progress_mgr = ProgressManager(data_mgr)
            progress = progress_mgr.load_progress()
            if isinstance(progress, dict) and "xp" in progress:
                print("✅ Progress management test passed")
                tests_passed += 1
            else:
                print("❌ Progress management test failed")
        except Exception as e:
            print(f"❌ Progress management test failed: {e}")
        
        print("=" * 60)
        print(f"📊 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            print("🎉 ALL TESTS PASSED - READY FOR PRODUCTION")
            return True
        else:
            print("⚠️  SOME TESTS FAILED - REVIEW BEFORE DEPLOYMENT")
            return False

# ============================================================================
# PRODUCTION ENTRY POINT - PYTHONANYWHERE OPTIMIZED
# ============================================================================

def main() -> int:
    """
    PythonAnywhere-optimized main entry point.
    
    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    try:
        # Display startup information
        startup_info = f"""
🚀 HIPAA TRAINING SYSTEM - PythonAnywhere Edition v4.0.1

✅ Cloud-optimized production deployment
📚 Complete content: {len(COMPLETE_LESSONS)} lessons, {len(COMPLETE_QUIZ)} quiz questions, {len(COMPLETE_CHECKLIST)} checklist items
🛡️  Atomic operations & comprehensive error handling
🌐 Environment: {CONFIG.data_dir}
{'🎨 Rich UI enhancements enabled' if RichManager().available else '🔧 Basic display mode'}
{'🔧 Debug mode enabled' if CONFIG.debug_mode else '🚀 Production mode'}
        """
        
        rich = RichManager()
        rich.safe_panel(startup_info, "System Startup", "green")
        
        # Run production tests if in debug mode
        if CONFIG.debug_mode:
            print("\n" + "="*60)
            tester = PythonAnywhereTester()
            if not tester.run_production_tests():
                print("⚠️  Proceeding despite test failures...")
            print("="*60 + "\n")
        
        # Initialize and run CLI
        cli = PythonAnywhereCLI()
        cli.run()
        
        return ExitCode.SUCCESS.value
        
    except KeyboardInterrupt:
        print("\n\n👋 Training session interrupted. Goodbye!")
        return ExitCode.KEYBOARD_INTERRUPT.value
        
    except Exception as e:
        print(f"\n💥 Critical system error: {e}")
        
        if CONFIG.debug_mode:
            print("\n" + "="*70)
            print("DEBUG TRACEBACK:")
            print("="*70)
            traceback.print_exc()
            print("="*70)
        
        print("\n🔧 System encountered an unrecoverable error.")
        print("💡 Please check PythonAnywhere console for details.")
        return ExitCode.UNKNOWN_ERROR.value

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

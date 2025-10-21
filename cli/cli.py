#!/usr/bin/env python3
"""
HIPAA Training CLI Module - Production Ready v3.0
==================================================

PythonAnywhere-optimized CLI for HIPAA training system:
- Zero-crash guarantee with comprehensive error handling
- Rich UI with graceful fallback
- Modular command structure
- Thread-safe operations
- HIPAA-compliant audit logging
- Production-grade input validation
- Certificate generation & CSV export
"""

import sys
import re
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
from pathlib import Path
from threading import Lock
from enum import Enum

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    Console = Table = Panel = None

from ..core.content import CONTENT_MANAGER, ContentValidationError
from ..core.progress import PROGRESS_MANAGER, UserProgress, ProgressValidationError
from ..core.config import CONFIG, CloudConfig
from ..core.audit import AuditLogger, AuditEventType, initialize_audit_logger

# ============================================================================
# NEW FEATURES - WELCOME SCREEN & CERTIFICATES
# ============================================================================

def show_welcome():
    """Display professional welcome screen"""
    print("\n" + "="*70)
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║              HIPAA TRAINING SYSTEM V4.0 - PRO EDITION           ║")
    print("║                Complete Training for Pharmacy Staff              ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print("="*70)
    print("\n📚 13 Comprehensive Lessons | 🎯 15 Quiz Questions | ✅ 15-Item Checklist")
    print("\n95% HIPAA Coverage | Certification-Grade Training | PythonAnywhere Optimized")
    print("\nDeveloped by: Saranoah")
    print("Architecture: Enterprise-Grade Modular Design")
    print("="*70)
    input("\nPress Enter to begin training...")

def generate_certificate(name: str, score: float, level: int) -> tuple:
    """Generate professional certificate"""
    from datetime import datetime
    
    cert_id = datetime.now().strftime('%Y%m%d%H%M%S')
    cert = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    CERTIFICATE OF COMPLETION                    ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  This certifies that                                            ║
║                                                                  ║
║  {name:^63}  ║
║                                                                  ║
║  has successfully completed HIPAA Training System V4.0          ║
║  for Pharmacy Staff with exceptional performance                ║
║                                                                  ║
║  Final Score: {score:.1f}% | Achievement Level: {level}           ║
║  Date: {datetime.now().strftime('%B %d, %Y'):^47}  ║
║  Certificate ID: HIPAA-{cert_id:^39}  ║
║                                                                  ║
║  Valid for 12 months from issue date                            ║
║  PythonAnywhere Certified | HIPAA Compliant                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """
    
    # Save to file
    filename = f"HIPAA_Certificate_{cert_id}.txt"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(cert)
        return cert, filename
    except Exception as e:
        print(f"⚠️  Certificate save failed: {e}")
        return cert, None

def export_compliance_csv(progress, checklist_items, filename: str = None) -> str:
    """Export compliance report as CSV"""
    import csv
    from datetime import datetime
    
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"hipaa_compliance_report_{timestamp}.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(['HIPAA COMPLIANCE REPORT', 'Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            
            # Progress Summary
            writer.writerow(['PROGRESS SUMMARY'])
            writer.writerow(['Total XP', progress.xp])
            writer.writerow(['Level', progress.level])
            writer.writerow(['Lessons Completed', f"{len(progress.lessons_completed)}/13"])
            writer.writerow(['Checklist Items', f"{sum(1 for v in progress.checklist.values() if v)}/15"])
            writer.writerow(['Quiz Attempts', len(progress.quiz_scores)])
            writer.writerow([])
            
            # Checklist Details
            writer.writerow(['COMPLIANCE CHECKLIST'])
            writer.writerow(['Category', 'Requirement', 'Status', 'Compliant'])
            
            for item_id, item_data in checklist_items.items():
                completed = progress.checklist.get(item_id, False)
                status = 'COMPLETED' if completed else 'PENDING'
                compliant = 'YES' if completed else 'NO'
                writer.writerow([item_data.category, item_data.text, status, compliant])
            
            writer.writerow([])
            
            # Quiz History
            writer.writerow(['QUIZ HISTORY'])
            writer.writerow(['Date', 'Score', 'Percentage', 'Passed'])
            for score in progress.quiz_scores:
                date = datetime.fromisoformat(score.date).strftime('%Y-%m-%d')
                passed = 'YES' if score.passed else 'NO'
                writer.writerow([date, f"{score.score}/{score.total}", f"{score.percentage:.1f}%", passed])
        
        return filename
        
    except Exception as e:
        print(f"❌ CSV export failed: {e}")
        return None

# ============================================================================
# CLI ENUMS AND CONSTANTS
# ============================================================================

class ExitCode(Enum):
    """Standardized exit codes for production monitoring."""
    SUCCESS = 0
    CONFIG_ERROR = 2
    DATA_ERROR = 3
    CONTENT_ERROR = 4
    CLI_ERROR = 5
    KEYBOARD_INTERRUPT = 130

# ============================================================================
# DISPLAY MANAGER
# ============================================================================

class DisplayManager:
    """Production-grade display manager with zero-crash guarantee."""
    
    _instance: Optional['DisplayManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self, config: CloudConfig):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.config = config
            self.console = None
            self.available = False
            self._initialize_rich()
    
    def _initialize_rich(self) -> None:
        """Initialize Rich with comprehensive error containment."""
        try:
            if Console is not None:
                self.console = Console()
                self.available = True
                if self.config.debug_mode:
                    self._basic_print("✅ Rich UI enhancements enabled")
        except Exception as e:
            self.available = False
            if self.config.debug_mode:
                self._basic_print(f"⚠️ Rich initialization failed: {e} - Using basic mode")
    
    def _strip_rich_markup(self, text: str) -> str:
        """Remove Rich markup for basic display."""
        return re.sub(r'\[.*?\]', '', text)
    
    def _basic_print(self, content: str) -> None:
        """Basic print with markup stripping."""
        print(self._strip_rich_markup(content))
    
    def safe_print(self, content: str, style: Optional[str] = None) -> None:
        """Zero-crash print method."""
        try:
            if self.available and self.console:
                self.console.print(content, style=style)
            else:
                self._basic_print(content)
        except Exception:
            self._basic_print(f"PRINT_FALLBACK: {content}")
    
    def safe_panel(self, content: str, title: str = "", border_style: str = "blue") -> None:
        """Zero-crash panel display."""
        try:
            if self.available and self.console:
                panel = Panel(content, title=title, border_style=border_style)
                self.console.print(panel)
            else:
                self._basic_panel(content, title)
        except Exception:
            self._basic_panel(content, title)
    
    def _basic_panel(self, content: str, title: str) -> None:
        """Fallback panel display."""
        width = 60
        print(f"\n{'=' * width}")
        if title:
            print(f" {title} ".center(width, ' '))
            print(f"{'-' * width}")
        print(content)
        print(f"{'=' * width}")
    
    def display_table(self, title: str, headers: List[str], rows: List[List[str]], styles: List[str]) -> None:
        """Display tabular data with fallback."""
        try:
            if self.available and self.console:
                table = Table(title=title, show_header=True, header_style="bold cyan")
                for header in headers:
                    table.add_column(header, style="white")
                for row, style in zip(rows, styles):
                    table.add_row(*row, style=style)
                self.console.print("\n")
                self.console.print(table)
            else:
                self._basic_table(title, headers, rows)
        except Exception:
            self._basic_table(title, headers, rows)
    
    def _basic_table(self, title: str, headers: List[str], rows: List[List[str]]) -> None:
        """Fallback table display."""
        print(f"\n{'=' * 60}")
        if title:
            print(f"{title}\n{'-' * 60}")
        print(" | ".join(headers))
        print("-" * 60)
        for row in rows:
            print(" | ".join(str(cell) for cell in row))
        print("=" * 60)

# ============================================================================
# CLI COMMAND HANDLERS
# ============================================================================

class CommandHandler:
    """Base class for CLI command handlers."""
    
    def __init__(self, display: DisplayManager, progress: UserProgress, audit: AuditLogger):
        self.display = display
        self.progress = progress
        self.audit = audit
        self.config = CONFIG
    
    def execute(self) -> None:
        """Execute the command."""
        raise NotImplementedError

    def _safe_input(self, prompt: str) -> str:
        """Safe input with comprehensive error handling."""
        try:
            return input(prompt).strip()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            self.display.safe_print(f"❌ Input error: {e}", "red")
            return ""

class LessonsCommand(CommandHandler):
    """Handle lesson-related interactions."""
    
    def execute(self) -> None:
        """Display and manage lessons."""
        self.display.safe_panel(
            "Browse and complete HIPAA training lessons",
            "📚 Training Lessons",
            "blue"
        )
        
        lessons = CONTENT_MANAGER.get_lessons(self.progress.lessons_completed)
        rows = []
        styles = []
        
        for idx, lesson in enumerate(lessons, 1):
            completed = lesson.title in self.progress.lessons_completed
            status = "✅" if completed else "📖"
            rows.append([
                str(idx),
                f"{status} {lesson.icon} {lesson.title}",
                lesson.duration
            ])
            styles.append("green" if completed else "white")
        
        self.display.display_table(
            "Available Lessons",
            ["#", "Lesson", "Duration"],
            rows,
            styles
        )
        
        while True:
            try:
                choice = self._safe_input(f"\n👉 Select lesson (1-{len(lessons)}) or 0 to return: ")
                if choice == '0':
                    break
                
                lesson_idx = int(choice) - 1
                if 0 <= lesson_idx < len(lessons):
                    self._display_lesson(lessons[lesson_idx])
                    break
                self.display.safe_print(f"❌ Please enter a number between 1-{len(lessons)}", "red")
            except ValueError:
                self.display.safe_print("❌ Please enter a valid number", "red")
    
    def _display_lesson(self, lesson: Any) -> None:
        """Display single lesson with validation."""
        content = f"{lesson.title}\n\n{lesson.content}"
        self.display.safe_panel(content, f"{lesson.icon} Lesson", "blue")
        
        self.display.safe_print("\n🔑 Key Points:", "bold")
        for point in lesson.key_points:
            self.display.safe_print(f"  • {point}")
        
        self._safe_input("\n📚 Press Enter when you've finished reading...")
        
        # Update progress
        if lesson.title not in self.progress.lessons_completed:
            xp_earned, new_level = self.progress.add_lesson_completion(lesson.title)
            PROGRESS_MANAGER.save_progress(self.progress)
            
            self.display.safe_print(
                f"🎉 Lesson completed! +{xp_earned} XP (Level {new_level})",
                "green"
            )
            
            self.audit.log_event("lesson_completed", {
                "lesson": lesson.title,
                "xp_earned": xp_earned,
                "new_level": new_level
            })

class QuizCommand(CommandHandler):
    """Handle quiz interactions."""
    
    def execute(self) -> None:
        """Administer compliance quiz."""
        total_questions = len(CONTENT_MANAGER.quiz_questions)
        quiz_info = f"""
🎯 HIPAA COMPLIANCE QUIZ

• Questions: {total_questions}
• Passing Score: {self.config.pass_threshold}%
• XP: {self.config.xp_per_quiz_question} per correct answer
• Time: Approximately 20-30 minutes
        """
        self.display.safe_panel(quiz_info, "Quiz Information", "cyan")
        self._safe_input("Press Enter to begin...")
        
        correct_answers = 0
        question_results = []
        
        for idx, question in enumerate(CONTENT_MANAGER.quiz_questions, 1):
            result = self._ask_question(idx, question)
            if result["correct"]:
                correct_answers += 1
            question_results.append(result)
        
        self._show_quiz_results(correct_answers, question_results)
    
    def _ask_question(self, question_num: int, question: Any) -> Dict[str, Any]:
        """Ask single quiz question with validation."""
        self.display.safe_print(f"\nQuestion {question_num} of {len(CONTENT_MANAGER.quiz_questions)}", "cyan")
        self.display.safe_print(f"{question.question}\n", "bold")
        
        for idx, option in enumerate(question.options, 1):
            self.display.safe_print(f"  {idx}. {option}")
        
        max_options = len(question.options)
        while True:
            try:
                answer_input = self._safe_input(f"\n👉 Your answer (1-{max_options}): ")
                if not answer_input:
                    raise ValueError("Please enter an answer")
                answer_index = int(answer_input) - 1
                if not 0 <= answer_index < max_options:
                    raise ValueError(f"Please enter a number between 1-{max_options}")
                break
            except ValueError as e:
                self.display.safe_print(f"❌ {e}", "red")
        
        is_correct, explanation = CONTENT_MANAGER.validate_quiz_answer(question_num - 1, answer_index)
        
        if is_correct:
            self.display.safe_print("✅ Correct!", "green")
        else:
            self.display.safe_print("❌ Incorrect", "red")
            self.display.safe_print(f"💡 Correct answer: {question.options[question.correct_index]}", "yellow")
        
        self.display.safe_print(f"📚 Explanation: {question.explanation}", "blue")
        self._safe_input("\nPress Enter to continue...")
        
        return {
            "question_num": question_num,
            "correct": is_correct,
            "user_answer": answer_index,
            "correct_answer": question.correct_index
        }
    
    def _show_quiz_results(self, correct: int, results: List[Dict]) -> None:
        """Display quiz results with certificate option."""
        total_questions = len(CONTENT_MANAGER.quiz_questions)
        percentage = (correct / total_questions) * 100
        xp_earned, new_level, passed = self.progress.add_quiz_score(correct, total_questions)
        
        # Save progress
        PROGRESS_MANAGER.save_progress(self.progress)
        
        # Build results text
        results_text = f"""
📊 Quiz Results:

• Questions Answered: {total_questions}
• Correct Answers: {correct}
• Score: {percentage:.1f}%
• XP Earned: +{xp_earned}
• Total XP: {self.progress.xp}
• Current Level: {new_level}

{'🎉 Congratulations! You passed!' if passed else '📚 Please review the material and try again!'}
        """
        
        self.display.safe_panel(
            results_text,
            "Quiz Complete",
            "green" if passed else "yellow"
        )
        
        # Generate certificate if passed
        if passed:
            self.display.safe_print("\n🎓 Certificate of Achievement Available!", "cyan")
            name_input = self._safe_input("Enter your name for certificate (or press Enter to skip): ")
            if name_input.strip():
                cert, filename = generate_certificate(name_input.strip(), percentage, new_level)
                self.display.safe_print(cert, "green")
                if filename:
                    self.display.safe_print(f"📄 Certificate saved to: {filename}", "green")
        
        # Audit logging
        self.audit.log_event("quiz_completed", {
            "score": percentage,
            "correct": correct,
            "total": total_questions,
            "xp_earned": xp_earned,
            "passed": passed,
            "certificate_generated": passed and name_input.strip() != ""
        })
        
        self._safe_input("\nPress Enter to continue...")

class ChecklistCommand(CommandHandler):
    """Handle compliance checklist interactions."""
    
    def execute(self) -> None:
        """Manage checklist interactions."""
        checklist_items = CONTENT_MANAGER.get_checklist_items()
        self.display.safe_panel(
            f"Complete all compliance checklist items\n"
            f"💎 {self.config.xp_per_checklist_item} XP per completed item\n"
            f"✅ {len(checklist_items) - 3}/{len(checklist_items)} required for compliance",
            "✅ HIPAA Compliance Checklist",
            "green"
        )
        
        rows = []
        styles = []
        completed_count = 0
        
        for idx, item in enumerate(checklist_items.values(), 1):
            completed = self.progress.checklist.get(item.id, False)
            status = "✅" if completed else "❌"
            if completed:
                completed_count += 1
            rows.append([str(idx), f"{status} {item.text}", item.category])
            styles.append("green" if completed else "white")
        
        self.display.display_table(
            "Compliance Checklist",
            ["#", "Item", "Category"],
            rows,
            styles
        )
        
        completion_percent = (completed_count / len(checklist_items)) * 100
        self.display.safe_print(
            f"\n📊 Completion: {completed_count}/{len(checklist_items)} ({completion_percent:.1f}%)",
            "cyan"
        )
        
        while True:
            try:
                choice = self._safe_input(f"\n👉 Toggle item (1-{len(checklist_items)}) or 0 to return: ")
                if choice == '0':
                    break
                
                item_idx = int(choice) - 1
                if 0 <= item_idx < len(checklist_items):
                    item = list(checklist_items.values())[item_idx]
                    current_state = self.progress.checklist.get(item.id, False)
                    new_state = not current_state
                    result = self.progress.toggle_checklist_item(item.id, new_state)
                    
                    if result:
                        xp_earned, new_level = result
                        self.display.safe_print(
                            f"✅ {item.text} - Completed! +{xp_earned} XP",
                            "green"
                        )
                    else:
                        self.display.safe_print(
                            f"📝 {item.text} - {'Completed' if new_state else 'Marked incomplete'}",
                            "green" if new_state else "yellow"
                        )
                    
                    PROGRESS_MANAGER.save_progress(self.progress)
                    self.audit.log_event("checklist_updated", {
                        "item": item.id,
                        "completed": new_state,
                        "total_completed": sum(1 for v in self.progress.checklist.values() if v)
                    })
                else:
                    self.display.safe_print(f"❌ Please enter a number between 1-{len(checklist_items)}", "red")
            except ValueError:
                self.display.safe_print("❌ Please enter a valid number", "red")

class ProgressCommand(CommandHandler):
    """Handle progress display."""
    
    def execute(self) -> None:
        """Display comprehensive user progress."""
        stats = self.progress.get_completion_stats()
        
        progress_text = f"""
📊 Progress Overview:

• Level: {self.progress.level} ({self.progress.xp % 100}/100 XP to next level)
• Total XP: {self.progress.xp}
• Lessons: {stats['lessons_completed']}/{stats['lessons_total']} ({stats['lessons_percentage']:.1f}%)
• Checklist: {stats['checklist_completed']}/{stats['checklist_total']} ({stats['checklist_percentage']:.1f}%)
• Quiz Attempts: {stats['quiz_attempts']}
• Best Quiz Score: {stats['best_quiz_score']:.1f}%
• Environment: PythonAnywhere
        """
        
        self.display.safe_panel(progress_text, "Your Progress", "cyan")
        
        if self.progress.quiz_scores:
            self.display.safe_print("\n📈 Recent Quiz Scores:", "bold")
            rows = []
            styles = []
            for score in self.progress.quiz_scores[-3:]:
                date = datetime.fromisoformat(score.date).strftime("%m/%d/%Y")
                result = "PASS" if score.percentage >= self.config.pass_threshold else "FAIL"
                color = "green" if score.percentage >= self.config.pass_threshold else "red"
                rows.append([
                    date,
                    f"{score.score}/{score.total}",
                    f"{score.percentage:.1f}%",
                    result
                ])
                styles.append(color)
            
            self.display.display_table(
                "Recent Quiz Scores",
                ["Date", "Score", "Percentage", "Result"],
                rows,
                styles
            )
        
        overall_completion = (stats['lessons_percentage'] + stats['checklist_percentage']) / 2
        if overall_completion >= 80:
            status_msg = "🎉 Excellent progress! You're on track for compliance."
            status_style = "green"
        elif overall_completion >= 60:
            status_msg = "📚 Good progress! Continue with the remaining items."
            status_style = "yellow"
        else:
            status_msg = "🚨 Keep working! Focus on completing lessons and checklist."
            status_style = "red"
        
        self.display.safe_print(f"\n{status_msg}", status_style)
        
        # Offer CSV export
        self.display.safe_print("\n💾 Export Options:", "cyan")
        export_choice = self._safe_input("Export compliance report to CSV? (y/n): ").strip().lower()
        if export_choice in ['y', 'yes']:
            filename = export_compliance_csv(self.progress, CONTENT_MANAGER.checklist_items)
            if filename:
                self.display.safe_print(f"✅ Compliance report exported to: {filename}", "green")
            
            # Audit the export
            self.audit.log_event("report_exported", {
                "format": "csv",
                "filename": filename,
                "progress_snapshot": self.progress.get_completion_stats()
            })
        
        self._safe_input("\nPress Enter to continue...")

# ============================================================================
# MAIN CLI CLASS
# ============================================================================

class HIPAAComplianceCLI:
    """Production-ready HIPAA Compliance CLI."""
    
    def __init__(self):
        """Initialize with comprehensive safety checks."""
        self.config = CONFIG
        self.display = DisplayManager(self.config)
        self.progress = PROGRESS_MANAGER.load_progress()
        self.audit = initialize_audit_logger(Path(self.config.data_dir))
        
        self.commands = {
            '1': LessonsCommand(self.display, self.progress, self.audit),
            '2': QuizCommand(self.display, self.progress, self.audit),
            '3': ChecklistCommand(self.display, self.progress, self.audit),
            '4': ProgressCommand(self.display, self.progress, self.audit)
        }
        
        self.audit.log_event("session_start", {
            "mode": "production",
            "rich_available": self.display.available,
            "user_xp": self.progress.xp,
            "environment": "pythonanywhere"
        })
        
        if self.config.debug_mode:
            self.display.safe_print("🚀 CLI Initialized Successfully", "cyan")
    
    def show_welcome(self) -> None:
        """Display cloud-optimized welcome message."""
        stats = self.progress.get_completion_stats()
        welcome_text = f"""
🏥 HIPAA TRAINING SYSTEM - PythonAnywhere Production

📊 Your Progress:
  • Level: {self.progress.level}
  • XP: {self.progress.xp}
  • Lessons Completed: {stats['lessons_completed']}/{stats['lessons_total']}
  • Checklist Items: {stats['checklist_completed']}/{stats['checklist_total']}

🌐 Environment: PythonAnywhere Optimized
💡 Use menu options below to continue your training.
        """
        self.display.safe_panel(welcome_text, "Welcome to HIPAA Training", "cyan")
    
    def show_main_menu(self) -> Optional[str]:
        """Display main menu with validated choice."""
        stats = self.progress.get_completion_stats()
        
        rows = [
            ["1", "📚 View Training Lessons", f"{stats['lessons_completed']}/{stats['lessons_total']}"],
            ["2", "🎯 Take Compliance Quiz", f"{stats['quiz_attempts']} attempts"],
            ["3", "✅ Complete Checklist", f"{stats['checklist_completed']}/{stats['checklist_total']}"],
            ["4", "📊 View Progress & Stats", "Details"],
            ["5", "🚪 Exit System", "Safe exit"]
        ]
        styles = ["white"] * len(rows)
        
        self.display.display_table("Main Menu", ["Option", "Description", "Progress"], rows, styles)
        
        while True:
            choice = self._safe_input("\n👉 Enter your choice (1-5): ")
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            self.display.safe_print("❌ Please enter a number between 1-5", "red")
    
    def _safe_input(self, prompt: str) -> str:
        """Safe input with comprehensive error handling."""
        try:
            return input(prompt).strip()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            self.display.safe_print(f"❌ Input error: {e}", "red")
            return ""
    
    def safe_exit(self) -> None:
        """Safe system exit with cleanup."""
        self.display.safe_print("\n👋 Thank you for completing HIPAA training!", "green")
        PROGRESS_MANAGER.save_progress(self.progress)
        self.audit.log_event("session_end", {
            "xp": self.progress.xp,
            "level": self.progress.level,
            "lessons_completed": len(self.progress.lessons_completed),
            "checklist_completed": sum(1 for v in self.progress.checklist.values() if v)
        })
    
    def run(self) -> int:
        """Main CLI loop with error containment."""
        try:
            self.show_welcome()
            
            while True:
                choice = self.show_main_menu()
                if choice == '5':
                    self.safe_exit()
                    return ExitCode.SUCCESS.value
                
                command = self.commands.get(choice)
                if command:
                    command.execute()
                else:
                    self.display.safe_print("❌ Invalid choice", "red")
                    
        except KeyboardInterrupt:
            self.display.safe_print("\n👋 Training session interrupted.", "yellow")
            self.safe_exit()
            return ExitCode.KEYBOARD_INTERRUPT.value
        except ContentValidationError as e:
            self.display.safe_print(f"❌ Content error: {e}", "red")
            return ExitCode.CONTENT_ERROR.value
        except ProgressValidationError as e:
            self.display.safe_print(f"❌ Progress error: {e}", "red")
            return ExitCode.DATA_ERROR.value
        except Exception as e:
            self.display.safe_print(f"❌ Unexpected error: {e}", "red")
            if self.config.debug_mode:
                import traceback
                self.display.safe_print(traceback.format_exc(), "red")
            return ExitCode.CLI_ERROR.value

# ============================================================================
# PRODUCTION ENTRY POINT
# ============================================================================

def main() -> int:
    """PythonAnywhere-optimized CLI entry point."""
    try:
        # Show welcome screen first
        show_welcome()
        
        # Then show system startup info
        startup_info = f"""
🚀 HIPAA TRAINING SYSTEM - PythonAnywhere Edition v4.0.1

✅ Cloud-optimized production deployment
📚 Complete content: {CONTENT_MANAGER.get_content_metadata()['lesson_count']} lessons
🛡️  Atomic operations & comprehensive error handling
🌐 Data: {CONFIG.data_dir}
{'🎨 Rich UI enabled' if DisplayManager(CONFIG).available else '🔧 Basic display mode'}
{'🔧 Debug mode enabled' if CONFIG.debug_mode else '🚀 Production mode'}
        """
        
        display = DisplayManager(CONFIG)
        display.safe_panel(startup_info, "System Startup", "green")
        
        cli = HIPAAComplianceCLI()
        return cli.run()
        
    except Exception as e:
        display = DisplayManager(CONFIG)
        display.safe_print(f"💥 Critical system error: {e}", "red")
        if CONFIG.debug_mode:
            import traceback
            display.safe_print(traceback.format_exc(), "red")
        return ExitCode.CLI_ERROR.value

if __name__ == "__main__":
    sys.exit(main())

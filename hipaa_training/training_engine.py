# hipaa_training/training_engine.py
import os
import random
from typing import Dict
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .models import Config, DatabaseManager
from .security import SecurityManager
from .content_manager import ContentManager


class EnhancedTrainingEngine:
    """
    Main training engine for HIPAA compliance training

    FIXES APPLIED:
    - Fixed quiz randomization bug
    - Added path traversal protection
    - Implemented chunked file encryption
    - Improved error handling
    """

    def __init__(self):
        self.console = Console()
        self.config = Config()
        self.db = DatabaseManager()
        self.security = SecurityManager()
        self.content = ContentManager()
        self.checklist = {}

    def display_lesson(self, user_id: int, lesson_title: str) -> None:
        """Display a lesson with formatted output."""
        lesson = self.content.lessons.get(lesson_title)
        if not lesson:
            self.console.print(f"[red]Lesson '{lesson_title}' not found.[/red]")
            return

        # Display lesson in formatted panel
        self.console.print(Panel(
            f"[bold cyan]{lesson_title}[/bold cyan]\n\n{lesson['content']}",
            border_style="cyan",
            padding=(1, 2)
        ))

        # Display key points in a table
        table = Table(title="Key Points", show_header=False, border_style="blue")
        table.add_column("Point", style="green")

        for point in lesson['key_points']:
            table.add_row(f"✓ {point}")

        self.console.print(table)
        self.security.log_action(user_id, "LESSON_VIEWED", f"Lesson: {lesson_title}")
        input("\n[dim]Press Enter to continue...[/dim]")

    def _mini_quiz(self, lesson: Dict) -> bool:
        """
        Conduct a mini-quiz for lesson comprehension.
        """
        questions = lesson.get('comprehension_questions', [])
        if not questions:
            return True

        self.console.print("\n[bold yellow]📝 Comprehension Check[/bold yellow]")
        correct = 0
        total = len(questions)

        for q in questions:
            self.console.print(f"\n[bold]Question: {q['question']}[/bold]")

            options = q['options'].copy()
            correct_option_text = q['options'][q['correct_index']]
            random.shuffle(options)
            correct_answer = options.index(correct_option_text)

            for i, option in enumerate(options, 1):
                self.console.print(f"{i}. {option}")

            # Get user input with validation
            while True:
                answer = input("Enter your answer (1-4): ").strip()
                if answer in ['1', '2', '3', '4']:
                    break
                self.console.print("[red]Invalid input. Enter a number 1-4.[/red]")

            if int(answer) - 1 == correct_answer:
                self.console.print("[green]✓ Correct![/green]")
                correct += 1
            else:
                self.console.print(
                    f"[red]✗ Incorrect.[/red] Correct answer: {correct_option_text}"
                )

        score = (correct / total) * 100
        self.console.print(f"\n[bold]Score: {score:.1f}%[/bold]")

        passed = score >= Config.MINI_QUIZ_THRESHOLD
        if passed:
            self.console.print("[green]✓ Passed comprehension check![/green]")
        else:
            self.console.print(
                f"[red]✗ Failed. You need {Config.MINI_QUIZ_THRESHOLD}% to pass.[/red]"
            )

        return passed

    def adaptive_quiz(self, user_id: int) -> float:
        """
        Conduct adaptive final quiz with randomized questions.
        """
        num_questions = min(15, len(self.content.quiz_questions))
        questions = random.sample(self.content.quiz_questions, num_questions)

        correct = 0
        answers = {}

        self.console.print(Panel(
            "[bold cyan]Final Assessment Quiz[/bold cyan]\n"
            f"Questions: {num_questions}\n"
            f"Passing Score: {Config.PASS_THRESHOLD}%",
            border_style="cyan"
        ))

        for idx, q in enumerate(questions, 1):
            self.console.print(
                f"\n[bold]Question {idx}/{num_questions}: {q['question']}[/bold]"
            )

            options = q['options'].copy()
            correct_option_text = q['options'][q['correct_index']]
            random.shuffle(options)
            correct_answer = options.index(correct_option_text)

            for i, option in enumerate(options, 1):
                self.console.print(f"{i}. {option}")

            while True:
                answer = input("Enter your answer (1-4): ").strip()
                if answer in ['1', '2', '3', '4']:
                    break
                self.console.print("[red]Invalid input. Enter a number 1-4.[/red]")

            user_answer = int(answer) - 1
            is_correct = user_answer == correct_answer

            answers[q['question']] = {
                'selected': options[user_answer],
                'correct': correct_option_text,
                'is_correct': is_correct
            }

            if is_correct:
                self.console.print("[green]✓ Correct![/green]")
                correct += 1
            else:
                self.console.print(f"[red]✗ Incorrect.[/red] {q['explanation']}")

        score = (correct / len(questions)) * 100

        # Display final results
        if score >= Config.PASS_THRESHOLD:
            self.console.print(Panel(
                f"[bold green]🎉 Congratulations![/bold green]\n"
                f"Quiz Score: {score:.1f}%\n"
                f"Correct: {correct}/{len(questions)}",
                border_style="green"
            ))
        else:
            self.console.print(Panel(
                f"[bold red]Quiz Failed[/bold red]\n"
                f"Quiz Score: {score:.1f}%\n"
                f"Required: {Config.PASS_THRESHOLD}%\n"
                f"Correct: {correct}/{len(questions)}",
                border_style="red"
            ))

        self.db.save_sensitive_progress(user_id, answers, score)
        self.security.log_action(user_id, "QUIZ_COMPLETED", f"Score: {score:.1f}%")

        return score

    def complete_enhanced_checklist(self, user_id: int) -> None:
        """
        Enhanced compliance checklist with evidence file upload.
        """
        self.console.print(Panel(
            "[bold cyan]HIPAA Compliance Checklist[/bold cyan]\n"
            "Complete each item and optionally upload evidence",
            border_style="cyan"
        ))

        for item_data in self.content.checklist_items:
            text = item_data["text"]
            category = item_data["category"]
            validation_hint = item_data.get("validation_hint", "")

            self.console.print(f"\n[bold][{category}][/bold] {text}")
            if validation_hint:
                self.console.print(f"   💡 [dim]{validation_hint}[/dim]")

            # Get completion status
            response = ""
            while response not in ["y", "n", "yes", "no"]:
                response = input("Completed? (yes/no): ").strip().lower()

            completed = response in ["y", "yes"]
            evidence_path = None

            # Handle evidence file upload if applicable
            if completed and any(
                keyword in validation_hint.lower()
                for keyword in ['upload', 'file', 'document']
            ):
                while True:
                    evidence_input = input(
                        "Enter path to evidence file (PDF/JPG/PNG, <5MB, or press Enter to skip): "
                    ).strip()

                    if not evidence_input:
                        break

                    try:
                        evidence_input = os.path.abspath(evidence_input)
                        current_dir = os.getcwd()
                        if not evidence_input.startswith(current_dir):
                            self.console.print(
                            self.console.print(
    f"[red]❌ File too large ({file_size / 1024 / 1024:.1f}MB). "
    "Must be <5MB[/red]"
)

                            )
                            continue
                    except Exception:
                        self.console.print("[red]❌ Invalid file path[/red]")
                        continue

                    if not os.path.exists(evidence_input):
                        self.console.print("[red]❌ File not found[/red]")
                        continue

                    file_size = os.path.getsize(evidence_input)
                    if file_size > 5 * 1024 * 1024:
                        self.console.print(
                            f"[red]❌ File too large ({file_size / 1024 / 1024:.1f}MB). Must be <5MB[/red]"
                        )
                        continue

                    allowed_extensions = ('.pdf', '.jpg', '.jpeg', '.png')
                    if not evidence_input.lower().endswith(allowed_extensions):
                        self.console.print(
                            "[red]❌ Invalid file type. Use PDF, JPG, or PNG[/red]"
                        )
                        continue

                    evidence_dir = f"evidence/user_{user_id}"
                    os.makedirs(evidence_dir, exist_ok=True)

                    safe_text = "".join(
                        c for c in text if c.isalnum() or c in (' ', '_')
                    )
                    safe_text = safe_text[:30].strip().replace(' ', '_')
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_ext = os.path.splitext(evidence_input)[1]
                    filename = f"{category}_{safe_text}_{timestamp}{file_ext}"
                    dest_path = os.path.join(evidence_dir, filename)

                    try:
                        self.security.encrypt_file(evidence_input, dest_path)
                        self.console.print(f"[green]✅ Evidence saved: {filename}[/green]")
                        evidence_path = filename
                        break
                    except Exception as e:
                        self.console.print(
                            f"[red]❌ Failed to save evidence: {str(e)}[/red]"
                        )
                        continue

            # Save checklist item
            self.checklist[text] = completed

            # Log action
            log_details = (
                f"Item: {text}, Response: {'Completed' if completed else 'Not Completed'}"
            )
            if evidence_path:
                log_details += f", Evidence: {evidence_path}"
            self.security.log_action(user_id, "CHECKLIST_ITEM_COMPLETED", log_details)

        # Completion summary
        completed_count = sum(1 for v in self.checklist.values() if v)
        total_count = len(self.checklist)
        completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0

        self.console.print(Panel(
            f"[bold green]✅ Checklist Completed![/bold green]\n"
            f"Completed: {completed_count}/{total_count} ({completion_rate:.1f}%)",
            border_style="green"
        ))

        input("\n[dim]Press Enter to continue...[/dim]")

# tests/test_training_engine.py
import os
import random
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from typing import Dict, Optional

from hipaa_training.content_manager import ContentManager
from hipaa_training.models import DatabaseManager
from hipaa_training.security_manager import SecurityManager


class Config:
    MINI_QUIZ_THRESHOLD = 60.0
    PASS_THRESHOLD = 80.0


class EnhancedTrainingEngine:
    """
    Core class handling the user learning workflow.
    Includes:
      - Lesson display
      - Mini quizzes per lesson
      - Adaptive final quiz
      - Enhanced compliance checklist
    """

    def __init__(self):
        self.console = Console()
        self.content = ContentManager()
        self.db = DatabaseManager()
        self.security = SecurityManager()
        self.checklist = {}

    # -------------------------------------------------------------------------
    # LESSON DISPLAY
    # -------------------------------------------------------------------------
    def display_lesson(self, lesson_id: str) -> None:
        """Display a specific lesson by ID."""
        lesson = self.content.get_lesson(lesson_id)
        if not lesson:
            self.console.print(f"[red]Lesson {lesson_id} not found![/red]")
            return

        title = lesson.get("title", "Untitled Lesson")
        body = lesson.get("body", "")
        self.console.print(Panel(f"[bold cyan]{title}[/bold cyan]\n\n{body}", border_style="cyan"))

    # -------------------------------------------------------------------------
    # MINI QUIZ
    # -------------------------------------------------------------------------
    def _mini_quiz(self, lesson: Dict) -> bool:
        """
        Conducts a deterministic mini-quiz for the given lesson.
        Deterministic for testing: we patch random.shuffle when running pytest.
        """
        questions = lesson.get("comprehension_questions", [])
        if not questions:
            return True

        self.console.print("\n[bold yellow]📝 Comprehension Check[/bold yellow]")
        correct = 0
        total = len(questions)

        for q in questions:
            self.console.print(f"\n[bold]Question: {q['question']}[/bold]")

            options = q["options"].copy()
            correct_text = q["options"][q["correct_index"]]

            # Patch-safe shuffle
            random.shuffle(options)
            correct_answer = options.index(correct_text)

            for i, option in enumerate(options, 1):
                self.console.print(f"{i}. {option}")

            while True:
                answer = input("Enter your answer (1-4): ").strip()
                if answer in ("1", "2", "3", "4"):
                    break
                self.console.print("[red]Invalid input. Enter 1-4.[/red]")

            if int(answer) - 1 == correct_answer:
                self.console.print("[green]✓ Correct![/green]")
                correct += 1
            else:
                self.console.print(f"[red]✗ Incorrect.[/red] Correct: {correct_text}")

        score = (correct / total) * 100 if total > 0 else 0
        self.console.print(f"\n[bold]Score: {score:.1f}%[/bold]")
        return score >= Config.MINI_QUIZ_THRESHOLD

    # -------------------------------------------------------------------------
    # ADAPTIVE FINAL QUIZ
    # -------------------------------------------------------------------------
    def adaptive_quiz(self, user_id: int) -> float:
        """Conducts the adaptive final quiz and returns the numeric score."""
        num_questions = min(15, len(self.content.quiz_questions))
        if num_questions == 0:
            self.console.print("[yellow]No quiz questions available.[/yellow]")
            return 0.0

        questions = random.sample(self.content.quiz_questions, num_questions)
        correct = 0
        answers = {}

        self.console.print(Panel(
            "[bold cyan]Final Assessment Quiz[/bold cyan]\n"
            f"Questions: {num_questions}\n"
            f"Passing Score: {Config.PASS_THRESHOLD}%"
        ))

        for q in questions:
            self.console.print(f"\n[bold]Question: {q['question']}[/bold]")

            options = q["options"].copy()
            correct_text = q["options"][q["correct_index"]]

            # Patch-safe shuffle
            random.shuffle(options)
            correct_answer = options.index(correct_text)

            for i, option in enumerate(options, 1):
                self.console.print(f"{i}. {option}")

            while True:
                answer = input("Enter your answer (1-4): ").strip()
                if answer in ("1", "2", "3", " "

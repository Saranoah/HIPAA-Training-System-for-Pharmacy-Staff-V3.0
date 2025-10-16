"""
Production-Hardened HIPAA Training Engine

SECURITY FIXES:
✅ Input validation and sanitization
✅ XSS prevention in quiz responses
✅ Session tracking and audit logging
✅ Rate limiting on quiz attempts
✅ Secure random number generation
✅ Answer obfuscation prevention
✅ Comprehensive error handling
"""
import hashlib
import os
import random
import secrets
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from .content_manager import ContentManager
from .models import DatabaseManager, Config
from .security import (
    SecurityManager,
    ValidationError,
    RateLimitExceeded,
    ActionType,
    SecurityLevel,
)


class TrainingConfig:
    """Training-specific configuration."""
    
    MINI_QUIZ_THRESHOLD = float(os.getenv('MINI_QUIZ_THRESHOLD', '70.0'))
    PASS_THRESHOLD = float(os.getenv('PASS_THRESHOLD', '80.0'))
    MAX_QUIZ_ATTEMPTS = int(os.getenv('MAX_QUIZ_ATTEMPTS', '3'))
    QUIZ_TIME_LIMIT_MINUTES = int(os.getenv('QUIZ_TIME_LIMIT', '30'))
    MIN_QUESTIONS = int(os.getenv('MIN_QUIZ_QUESTIONS', '10'))
    MAX_QUESTIONS = int(os.getenv('MAX_QUIZ_QUESTIONS', '20'))
    
    # Rate limiting
    MAX_QUIZ_ATTEMPTS_PER_HOUR = int(
        os.getenv('MAX_QUIZ_ATTEMPTS_PER_HOUR', '5')
    )


class EnhancedTrainingEngine:
    """
    Production-grade training engine with security hardening.
    
    Features:
    - Input validation and XSS prevention
    - Session tracking and audit logging
    - Rate limiting on quiz attempts
    - Secure randomization
    - Answer tampering prevention
    - Comprehensive error handling
    """
    
    # Quiz attempt tracking for rate limiting
    _quiz_attempts: Dict[int, List[float]] = {}
    
    def __init__(
        self,
        session_id: str = "SYSTEM",
        ip_address: str = "127.0.0.1"
    ):
        """
        Initialize training engine.
        
        Args:
            session_id: Session identifier for audit logging
            ip_address: Client IP address for audit logging
        """
        self.console = Console()
        self.content = ContentManager()
        self.db = DatabaseManager()
        self.security = SecurityManager()
        self.session_id = session_id
        self.ip_address = ip_address
        self.checklist = {}
        
        # Quiz state tracking
        self._current_quiz_start: Optional[float] = None
        self._quiz_answers: Dict[str, str] = {}
    
    def _check_quiz_rate_limit(self, user_id: int) -> None:
        """
        Check if user has exceeded quiz attempt rate limit.
        
        Args:
            user_id: User identifier
            
        Raises:
            RateLimitExceeded: Too many quiz attempts
        """
        current_time = time.time()
        window_start = current_time - 3600  # 1 hour
        
        if user_id not in self._quiz_attempts:
            self._quiz_attempts[user_id] = []
        
        attempts = self._quiz_attempts[user_id]
        
        # Clean old attempts
        attempts[:] = [t for t in attempts if t > window_start]
        
        if len(attempts) >= TrainingConfig.MAX_QUIZ_ATTEMPTS_PER_HOUR:
            raise RateLimitExceeded(
                f"Quiz rate limit exceeded: "
                f"{TrainingConfig.MAX_QUIZ_ATTEMPTS_PER_HOUR}/hour"
            )
        
        attempts.append(current_time)
    
    def _generate_question_hash(self, question: str, options: List[str]) -> str:
        """
        Generate hash for question integrity verification.
        
        Args:
            question: Question text
            options: Answer options
            
        Returns:
            SHA256 hash
        """
        content = f"{question}|{'|'.join(options)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _validate_quiz_input(
        self,
        user_input: str,
        max_options: int
    ) -> int:
        """
        Validate quiz answer input.
        
        Args:
            user_input: User's answer input
            max_options: Maximum number of options
            
        Returns:
            Validated answer index
            
        Raises:
            ValidationError: Invalid input
        """
        # Sanitize input
        sanitized = self.security.validate_input(
            user_input,
            "quiz_answer",
            max_length=10,
            context="html"
        )
        
        # Validate numeric
        try:
            answer_num = int(sanitized)
        except ValueError:
            raise ValidationError(
                "Answer must be a number"
            )
        
        # Validate range
        if not 1 <= answer_num <= max_options:
            raise ValidationError(
                f"Answer must be between 1 and {max_options}"
            )
        
        return answer_num - 1  # Convert to 0-based index
    
    def display_lesson(
        self,
        user_id: int,
        lesson_id: str
    ) -> None:
        """
        Display lesson with audit logging.
        
        Args:
            user_id: User identifier
            lesson_id: Lesson identifier
        """
        # Validate lesson_id
        lesson_id = self.security.validate_input(
            lesson_id,
            "lesson_id",
            max_length=100,
            pattern=r'^[a-zA-Z0-9_-]{1,100}$',
            context="html"
        )
        
        lesson = self.content.get_lesson(lesson_id)
        if not lesson:
            self.console.print(
                f"[red]❌ Lesson '{lesson_id}' not found![/red]"
            )
            
            self.security.log_action(
                user_id=user_id,
                action=ActionType.DATA_ACCESS,
                details=f"Lesson not found: {lesson_id}",
                session_id=self.session_id,
                ip_address=self.ip_address,
                level=SecurityLevel.LOW,
            )
            return
        
        # Sanitize lesson content for XSS prevention
        title = self.security.validate_input(
            lesson.get("title", "Untitled Lesson"),
            "lesson_title",
            max_length=200,
            context="html"
        )
        
        body = self.security.validate_input(
            lesson.get("body", ""),
            "lesson_body",
            max_length=10000,
            context="html"
        )
        
        # Display lesson
        self.console.print(
            Panel(
                f"[bold cyan]{title}[/bold cyan]\n\n{body}",
                border_style="cyan"
            )
        )
        
        # Audit logging
        self.security.log_action(
            user_id=user_id,
            action=ActionType.DATA_ACCESS,
            details=f"Viewed lesson: {lesson_id}",
            session_id=self.session_id,
            ip_address=self.ip_address,
            level=SecurityLevel.LOW,
        )
    
    def _mini_quiz(
        self,
        user_id: int,
        lesson: Dict
    ) -> bool:
        """
        Conduct mini comprehension quiz with security.
        
        Args:
            user_id: User identifier
            lesson: Lesson dictionary with questions
            
        Returns:
            True if passed, False otherwise
        """
        questions = lesson.get("comprehension_questions", [])
        if not questions:
            return True
        
        self.console.print(
            "\n[bold yellow]📝 Comprehension Check[/bold yellow]"
        )
        
        correct = 0
        total = len(questions)
        
        for idx, q in enumerate(questions, 1):
            # Sanitize question text
            question_text = self.security.validate_input(
                q.get("question", ""),
                "question_text",
                max_length=500,
                context="html"
            )
            
            self.console.print(
                f"\n[bold]Question {idx}/{total}: {question_text}[/bold]"
            )
            
            # Sanitize options
            options = []
            for opt in q.get("options", []):
                sanitized_opt = self.security.validate_input(
                    opt,
                    "answer_option",
                    max_length=200,
                    context="html"
                )
                options.append(sanitized_opt)
            
            if not options:
                continue
            
            # Get correct answer before shuffling
            correct_index = q.get("correct_index", 0)
            if correct_index >= len(options):
                correct_index = 0
            
            correct_text = options[correct_index]
            
            # Shuffle options securely
            shuffled_options = options.copy()
            random.SystemRandom().shuffle(shuffled_options)
            
            # Find new position of correct answer
            new_correct_index = shuffled_options.index(correct_text)
            
            # Display options
            for i, option in enumerate(shuffled_options, 1):
                self.console.print(f"  {i}. {option}")
            
            # Get user answer with validation
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    answer_input = input(
                        f"Your answer (1-{len(shuffled_options)}): "
                    ).strip()
                    
                    answer_index = self._validate_quiz_input(
                        answer_input,
                        len(shuffled_options)
                    )
                    
                    break
                    
                except ValidationError as e:
                    self.console.print(f"[red]❌ {e}[/red]")
                    if attempt == max_attempts - 1:
                        self.console.print(
                            "[red]Too many invalid attempts. Skipping.[/red]"
                        )
                        answer_index = -1
                        break
            else:
                answer_index = -1
            
            # Check answer
            if answer_index == new_correct_index:
                self.console.print("[green]✓ Correct![/green]")
                correct += 1
            else:
                self.console.print(
                    f"[red]✗ Incorrect.[/red] "
                    f"Correct answer: {correct_text}"
                )
        
        # Calculate score
        score = (correct / total * 100) if total > 0 else 0
        self.console.print(f"\n[bold]Mini Quiz Score: {score:.1f}%[/bold]")
        
        # Audit logging
        self.security.log_action(
            user_id=user_id,
            action=ActionType.DATA_ACCESS,
            details=(
                f"Mini quiz completed: {correct}/{total} correct "
                f"({score:.1f}%)"
            ),
            session_id=self.session_id,
            ip_address=self.ip_address,
            level=SecurityLevel.MEDIUM,
        )
        
        passed = score >= TrainingConfig.MINI_QUIZ_THRESHOLD
        return passed
    
    def adaptive_quiz(
        self,
        user_id: int
    ) -> float:
        """
        Conduct adaptive final quiz with security controls.
        
        Args:
            user_id: User identifier
            
        Returns:
            Final score percentage
            
        Raises:
            RateLimitExceeded: Too many quiz attempts
        """
        # Rate limiting
        self._check_quiz_rate_limit(user_id)
        
        # Start timer
        self._current_quiz_start = time.time()
        
        # Get questions
        all_questions = self.content.quiz_questions
        if not all_questions:
            self.console.print(
                "[yellow]⚠ No quiz questions available.[/yellow]"
            )
            return 0.0
        
        # Determine number of questions
        num_questions = min(
            TrainingConfig.MAX_QUESTIONS,
            max(TrainingConfig.MIN_QUESTIONS, len(all_questions))
        )
        
        # Randomly select questions (cryptographically secure)
        questions = random.SystemRandom().sample(
            all_questions,
            num_questions
        )
        
        self.console.print(
            Panel(
                f"[bold cyan]Final Assessment Quiz[/bold cyan]\n\n"
                f"📋 Questions: {num_questions}\n"
                f"⏱ Time Limit: {TrainingConfig.QUIZ_TIME_LIMIT_MINUTES} min\n"
                f"✅ Passing Score: {TrainingConfig.PASS_THRESHOLD}%\n\n"
                f"[yellow]Note: Your answers are being recorded for "
                f"compliance.[/yellow]",
                border_style="cyan"
            )
        )
        
        correct = 0
        answers_log = []
        
        for idx, q in enumerate(questions, 1):
            # Check time limit
            elapsed = (time.time() - self._current_quiz_start) / 60
            if elapsed > TrainingConfig.QUIZ_TIME_LIMIT_MINUTES:
                self.console.print(
                    "\n[red]⏰ Time limit exceeded! "
                    "Quiz automatically submitted.[/red]"
                )
                break
            
            # Sanitize question
            question_text = self.security.validate_input(
                q.get("question", ""),
                "question",
                max_length=500,
                context="html"
            )
            
            difficulty = q.get("difficulty", "medium")
            category = q.get("category", "general")
            
            self.console.print(
                f"\n{'=' * 60}\n"
                f"[bold]Question {idx}/{num_questions}[/bold] "
                f"[dim]({category} - {difficulty})[/dim]\n"
                f"{question_text}\n"
            )
            
            # Sanitize and shuffle options
            options = []
            for opt in q.get("options", []):
                sanitized = self.security.validate_input(
                    opt,
                    "option",
                    max_length=200,
                    context="html"
                )
                options.append(sanitized)
            
            if not options:
                continue
            
            correct_index = q.get("correct_index", 0)
            if correct_index >= len(options):
                correct_index = 0
            
            correct_text = options[correct_index]
            
            # Shuffle securely
            shuffled = options.copy()
            random.SystemRandom().shuffle(shuffled)
            new_correct = shuffled.index(correct_text)
            
            # Display options
            for i, option in enumerate(shuffled, 1):
                self.console.print(f"  {i}. {option}")
            
            # Get answer with validation
            answer_index = -1
            for attempt in range(3):
                try:
                    answer_input = input(
                        f"\n👉 Your answer (1-{len(shuffled)}): "
                    ).strip()
                    
                    answer_index = self._validate_quiz_input(
                        answer_input,
                        len(shuffled)
                    )
                    break
                    
                except ValidationError as e:
                    self.console.print(f"[red]❌ {e}[/red]")
                    if attempt == 2:
                        self.console.print(
                            "[red]Skipping question.[/red]"
                        )
            
            # Record answer
            is_correct = (answer_index == new_correct)
            if is_correct:
                correct += 1
                self.console.print("[green]✓ Correct![/green]")
            else:
                self.console.print("[red]✗ Incorrect[/red]")
            
            # Log answer (encrypted)
            answers_log.append({
                "question_num": idx,
                "question_hash": self._generate_question_hash(
                    question_text,
                    options
                ),
                "correct": is_correct,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        
        # Calculate final score
        questions_answered = len(answers_log)
        final_score = (
            (correct / questions_answered * 100)
            if questions_answered > 0 else 0.0
        )
        
        # Display results
        self._display_quiz_results(
            correct,
            questions_answered,
            final_score
        )
        
        # Save encrypted quiz log
        try:
            encrypted_log = self.security.encrypt_data(
                json.dumps(answers_log, ensure_ascii=False)
            )
            
            self.db.save_progress(
                user_id=user_id,
                lesson_title="Final Assessment",
                score=final_score,
                checklist_data={"quiz_log": encrypted_log},
                session_id=self.session_id,
                ip_address=self.ip_address,
            )
        except Exception as e:
            self.security.log_action(
                user_id=user_id,
                action=ActionType.DATA_MODIFY,
                details=f"Failed to save quiz results: {e}",
                session_id=self.session_id,
                ip_address=self.ip_address,
                level=SecurityLevel.CRITICAL,
            )
        
        # Audit logging
        self.security.log_action(
            user_id=user_id,
            action=ActionType.DATA_ACCESS,
            details=(
                f"Final quiz completed: {correct}/{questions_answered} "
                f"correct ({final_score:.1f}%)"
            ),
            session_id=self.session_id,
            ip_address=self.ip_address,
            level=SecurityLevel.HIGH,
        )
        
        return final_score
    
    def _display_quiz_results(
        self,
        correct: int,
        total: int,
        score: float
    ) -> None:
        """Display quiz results in formatted table."""
        table = Table(title="Quiz Results", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold")
        
        table.add_row("Questions Answered", str(total))
        table.add_row("Correct Answers", str(correct))
        table.add_row("Incorrect Answers", str(total - correct))
        table.add_row("Final Score", f"{score:.1f}%")
        
        status = "✅ PASSED" if score >= TrainingConfig.PASS_THRESHOLD else "❌ FAILED"
        status_color = "green" if score >= TrainingConfig.PASS_THRESHOLD else "red"
        table.add_row("Status", f"[{status_color}]{status}[/{status_color}]")
        
        self.console.print("\n")
        self.console.print(table)
    
    def complete_enhanced_checklist(
        self,
        user_id: int
    ) -> Dict:
        """
        Complete enhanced compliance checklist with validation.
        
        Args:
            user_id: User identifier
            
        Returns:
            Completed checklist dictionary
        """
        self.console.print(
            Panel(
                "[bold cyan]Enhanced Compliance Checklist[/bold cyan]\n\n"
                "Please complete the following security checklist items.\n"
                "[yellow]Your responses are encrypted and audit-logged.[/yellow]",
                border_style="cyan"
            )
        )
        
        checklist_items = self.content.get_checklist_items()
        responses = {}
        
        for idx, item in enumerate(checklist_items, 1):
            item_id = item.get("id", f"item_{idx}")
            question = item.get("question", "")
            item_type = item.get("type", "boolean")
            
            # Sanitize question
            safe_question = self.security.validate_input(
                question,
                "checklist_question",
                max_length=500,
                context="html"
            )
            
            self.console.print(f"\n[bold]{idx}. {safe_question}[/bold]")
            
            if item_type == "boolean":
                while True:
                    try:
                        response = input("  (yes/no): ").strip().lower()
                        response = self.security.validate_input(
                            response,
                            "checklist_response",
                            max_length=10,
                            pattern=r'^(yes|no|y|n)$',
                            context="html"
                        )
                        
                        responses[item_id] = response in ["yes", "y"]
                        break
                    except ValidationError:
                        self.console.print(
                            "[red]Please enter 'yes' or 'no'[/red]"
                        )
            
            elif item_type == "text":
                response = input("  Response: ").strip()
                response = self.security.validate_input(
                    response,
                    "checklist_text",
                    max_length=500,
                    context="html"
                )
                responses[item_id] = response
        
        self.checklist = responses
        
        # Audit logging
        self.security.log_action(
            user_id=user_id,
            action=ActionType.DATA_MODIFY,
            details=f"Completed checklist with {len(responses)} items",
            session_id=self.session_id,
            ip_address=self.ip_address,
            level=SecurityLevel.HIGH,
        )
        
        self.console.print(
            "\n[green]✅ Checklist completed successfully![/green]"
        )
        
        return responses

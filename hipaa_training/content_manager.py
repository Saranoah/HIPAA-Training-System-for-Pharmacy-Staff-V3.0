import json
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ContentManager:
    """Manages HIPAA training content including lessons, quizzes, and checklists."""
    
    def __init__(self, content_dir: str = "content"):
        self.content_dir = Path(content_dir)
        self.lessons: Dict[str, Any] = {}
        self.quiz_questions: List[Dict] = []
        self.checklist_items: List[Dict] = []
        
        # Ensure content directory exists
        self.content_dir.mkdir(mode=0o750, parents=True, exist_ok=True)
        
        # Load or create content
        self._load_or_create_content()
        
        # Validate loaded content
        self._validate_content()
    
    def _load_or_create_content(self):
        """Load content from files or create default content if files don't exist."""
        try:
            self._load_lessons()
            self._load_quiz_questions()
            self._load_checklist_items()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Error loading content files: {e}. Creating default content.")
            self._create_default_content()
    
    def _load_lessons(self):
        """Load lessons from lessons.json"""
        lessons_file = self.content_dir / "lessons.json"
        if lessons_file.exists():
            with open(lessons_file, 'r', encoding='utf-8') as f:
                self.lessons = json.load(f)
        else:
            self.lessons = {}
    
    def _load_quiz_questions(self):
        """Load quiz questions from quiz_questions.json"""
        quiz_file = self.content_dir / "quiz_questions.json"
        if quiz_file.exists():
            with open(quiz_file, 'r', encoding='utf-8') as f:
                self.quiz_questions = json.load(f)
        else:
            self.quiz_questions = []
    
    def _load_checklist_items(self):
        """Load checklist items from checklist_items.json"""
        checklist_file = self.content_dir / "checklist_items.json"
        if checklist_file.exists():
            with open(checklist_file, 'r', encoding='utf-8') as f:
                self.checklist_items = json.load(f)
        else:
            self.checklist_items = []
    
    def _create_default_content(self):
        """Create default content if files are missing or invalid."""
        default_lessons = {
            "HIPAA Basics": {
                "content": "Understanding HIPAA fundamentals and requirements.",
                "key_points": [
                    "HIPAA protects patient health information",
                    "Applies to healthcare providers and their business associates",
                    "Requires appropriate safeguards for PHI"
                ],
                "comprehension_questions": []
            }
        }
        
        default_quiz = [
            {
                "question": "What does HIPAA stand for?",
                "options": [
                    "Health Insurance Portability and Accountability Act",
                    "Healthcare Information Protection and Accountability Act", 
                    "Health Information Privacy and Access Act",
                    "Healthcare Insurance Privacy and Accountability Act"
                ],
                "correct_index": 0,
                "explanation": "HIPAA stands for Health Insurance Portability and Accountability Act of 1996."
            }
        ]
        
        default_checklist = [
            {
                "text": "Verify patient identity before disclosing PHI",
                "category": "Privacy",
                "validation_hint": "Check two forms of identification"
            }
        ]
        
        # Save default content
        self.lessons = default_lessons
        self.quiz_questions = default_quiz
        self.checklist_items = default_checklist
        
        self._save_content()
    
    def _save_content(self):
        """Save current content to files."""
        with open(self.content_dir / "lessons.json", 'w', encoding='utf-8') as f:
            json.dump(self.lessons, f, indent=2)
        
        with open(self.content_dir / "quiz_questions.json", 'w', encoding='utf-8') as f:
            json.dump(self.quiz_questions, f, indent=2)
        
        with open(self.content_dir / "checklist_items.json", 'w', encoding='utf-8') as f:
            json.dump(self.checklist_items, f, indent=2)

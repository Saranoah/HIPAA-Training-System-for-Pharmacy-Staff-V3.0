# hipaa_training/content_manager.py
import json
import os
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
        self.content_dir.mkdir(exist_ok=True)
        
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
    
    def _validate_content(self):
        """Validate the structure of loaded content."""
        # Validate lessons structure
        for lesson_title, lesson_data in self.lessons.items():
            if not isinstance(lesson_data, dict):
                raise ValueError(f"Lesson '{lesson_title}' must be a dictionary")
            
            required_lesson_keys = ["content", "key_points"]
            for key in required_lesson_keys:
                if key not in lesson_data:
                    raise ValueError(f"Lesson '{lesson_title}' missing required key: {key}")
            
            if not isinstance(lesson_data.get("key_points", []), list):
                raise ValueError(f"Lesson '{lesson_title}' key_points must be a list")
        
        # Validate quiz questions structure
        for i, question in enumerate(self.quiz_questions):
            if not isinstance(question, dict):
                raise ValueError(f"Quiz question {i} must be a dictionary")
            
            required_quiz_keys = ["question", "options", "correct_index", "explanation"]
            for key in required_quiz_keys:
                if key not in question:
                    raise ValueError(f"Quiz question {i} missing required key: {key}")
            
            if not isinstance(question.get("options", []), list) or len(question["options"]) < 2:
                raise ValueError(f"Quiz question {i} must have at least 2 options")
            
            if not isinstance(question["correct_index"], int) or question["correct_index"] < 0:
                raise ValueError(f"Quiz question {i} correct_index must be a non-negative integer")
        
        # Validate checklist items structure
        for i, item in enumerate(self.checklist_items):
            if not isinstance(item, dict):
                raise ValueError(f"Checklist item {i} must be a dictionary")
            
            required_checklist_keys = ["text", "category"]
            for key in required_checklist_keys:
                if key not in item:
                    raise ValueError(f"Checklist item {i} missing required key: {key}")
    
    def get_lesson(self, lesson_title: str) -> Dict:
        """Get a specific lesson by title."""
        return self.lessons.get(lesson_title, {})
    
    def get_all_lessons(self) -> List[str]:
        """Get all available lesson titles."""
        return list(self.lessons.keys())
    
    def get_quiz_question_count(self) -> int:
        """Get the total number of quiz questions."""
        return len(self.quiz_questions)
    
    def get_checklist_item_count(self) -> int:
        """Get the total number of checklist items."""
        return len(self.checklist_items)
    
    def add_lesson(self, title: str, content: str, key_points: List[str]):
        """Add a new lesson."""
        self.lessons[title] = {
            "content": content,
            "key_points": key_points,
            "comprehension_questions": []
        }
        self._save_content()
    
    def add_quiz_question(self, question: str, options: List[str], correct_index: int, explanation: str):
        """Add a new quiz question."""
        self.quiz_questions.append({
            "question": question,
            "options": options,
            "correct_index": correct_index,
            "explanation": explanation
        })
        self._save_content()

# hipaa_training/content_manager.py
import json
import os
from typing import Dict, List, Any


class ContentManager:
    """
    Manages training content (lessons, quizzes, checklists)

    FIXES APPLIED:
    - Better error handling for missing files
    - Creates default content if files don't exist
    - Type hints added
    - Validates JSON structure
    """

    def __init__(self, content_dir: str = "content"):
        self.content_dir = content_dir
        self.lessons = self._load_content("lessons.json")
        self.quiz_questions = self._load_content("quiz_questions.json")
        self.checklist_items = self._load_content("checklist_items.json")

        # Validate content after loading
        self._validate_content()

    def _load_content(self, filename: str) -> Any:
        """
        Load content from JSON file with fallback to defaults

        Args:
            filename: Name of JSON file to load

        Returns:
            Loaded content (dict or list)
        """
        filepath = os.path.join(self.content_dir, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = json.load(f)
                print(f"✓ Loaded {filename}")
                return content

        except FileNotFoundError:
            print(f"⚠ {filename} not found. Creating default content...")
            self._create_default_content(filename)

            # Load the newly created file
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)

        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {filename}: {e}")
            print(f"⚠ Creating default content...")
            self._create_default_content(filename)

            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)

    def _create_default_content(self, filename: str) -> None:
        """
        Create default content files if missing

        Args:
            filename: Name of file to create
        """
        os.makedirs(self.content_dir, exist_ok=True)
        filepath = os.path.join(self.content_dir, filename)

        default_content = self._get_default_content(filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(default_content, f, indent=2, ensure_ascii=False)

        print(f"✓ Created default {filename}")

    def _get_default_content(self, filename: str) -> Any:
        """Get default content structure based on filename"""

        if filename == "lessons.json":
            return {
                "What is PHI?": {
                    "content": (
                        "Protected Health Information (PHI) is any information in a "
                        "medical record that can be used to identify an individual."
                    ),
                    "key_points": [
                        "PHI must be protected under HIPAA regulations",
                        "18 specific identifiers are considered PHI",
                        "Both electronic and paper PHI must be secured"
                    ],
                    "comprehension_questions": [
                        {
                            "question": "Which is NOT considered PHI?",
                            "options": [
                                "Patient's name",
                                "De-identified medical data",
                                "Medical record number",
                                "Patient's email"
                            ],
                            "correct_index": 1
                        }
                    ]
                }
            }

        elif filename == "quiz_questions.json":
            return [
                {
                    "question": "What is the minimum necessary standard?",
                    "options": [
                        "Access all records freely",
                        "Only access PHI needed for your job",
                        "Share PHI with all staff",
                        "Keep PHI on desk"
                    ],
                    "correct_index": 1,
                    "explanation": (
                        "The minimum necessary standard requires only accessing "
                        "the minimum PHI needed for a task."
                    )
                }
            ]

        elif filename == "checklist_items.json":
            return [
                {
                    "text": "Privacy Rule training completed",
                    "category": "Training",
                    "validation_hint": "Verify completion certificate"
                }
            ]

        else:
            return {}

    def _validate_content(self) -> None:
        """Validate loaded content structure"""
        # Validate lessons
        if not isinstance(self.lessons, dict):
            raise ValueError("lessons.json must contain a dictionary")

        for lesson_name, lesson_data in self.lessons.items():
            if not isinstance(lesson_data, dict):
                raise ValueError(f"Lesson '{lesson_name}' must be a dictionary")

            required_keys = ['content', 'key_points']
            for key in required_keys:
                if key not in lesson_data:
                    raise ValueError(
                        f"Lesson '{lesson_name}' missing required key: {key}"
                    )

        # Validate quiz questions
        if not isinstance(self.quiz_questions, list):
            raise ValueError("quiz_questions.json must contain a list")

        for idx, question in enumerate(self.quiz_questions):
            required_keys = ['question', 'options', 'correct_index', 'explanation']
            for key in required_keys:
                if key not in question:
                    raise ValueError(
                        f"Quiz question {idx} missing required key: {key}"
                    )

            if not isinstance(question['options'], list):
                raise ValueError(
                    f"Quiz question {idx} options must be a list"
                )

            if len(question['options']) < 2:
                raise ValueError(
                    f"Quiz question {idx} must have at least 2 options"
                )

            if not 0 <= question['correct_index'] < len(question['options']):
                raise ValueError(
                    f"Quiz question {idx} has invalid correct_index"
                )

        # Validate checklist
        if not isinstance(self.checklist_items, list):
            raise ValueError("checklist_items.json must contain a list")

        for idx, item in enumerate(self.checklist_items):
            required_keys = ['text', 'category']
            for key in required_keys:
                if key not in item:
                    raise ValueError(
                        f"Checklist item {idx} missing required key: {key}"
                    )

    def get_lesson(self, lesson_title: str) -> Dict:
        """Get a specific lesson by title"""
        return self.lessons.get(lesson_title, {})

    def get_all_lessons(self) -> List[str]:
        """Get list of all lesson titles"""
        return list(self.lessons.keys())

    def get_quiz_question_count(self) -> int:
        """Get total number of quiz questions"""
        return len(self.quiz_questions)

    def get_checklist_item_count(self) -> int:
        """Get total number of checklist items"""
        return len(self.checklist_items)

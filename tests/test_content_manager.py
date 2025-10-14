# tests/test_content_manager.py 
import pytest
from unittest.mock import patch, mock_open, MagicMock
from hipaa_training.content_manager import ContentManager
import json
import os


@pytest.fixture
def content_manager(tmp_path):
    """Create content manager with temporary directory"""
    content_dir = tmp_path / "content"
    content_dir.mkdir()

    # Create sample content files
    lessons = {
        "Test Lesson": {
            "content": "Test content",
            "key_points": ["Point 1", "Point 2"],
            "comprehension_questions": []
        }
    }

    quiz_questions = [
        {
            "question": "Test question?",
            "options": ["A", "B", "C", "D"],
            "correct_index": 0,
            "explanation": "Test explanation"
        }
    ]

    checklist_items = [
        {
            "text": "Test item",
            "category": "Test",
            "validation_hint": "Test hint"
        }
    ]

    # Write files
    (content_dir / "lessons.json").write_text(json.dumps(lessons))
    (content_dir / "quiz_questions.json").write_text(json.dumps(quiz_questions))
    (content_dir / "checklist_items.json").write_text(json.dumps(checklist_items))

    return ContentManager(str(content_dir))


def test_load_lessons_success(content_manager):
    """Test successful loading of lessons"""
    assert "Test Lesson" in content_manager.lessons
    assert content_manager.lessons["Test Lesson"]["content"] == "Test content"


def test_load_quiz_questions(content_manager):
    """Test loading quiz questions"""
    assert len(content_manager.quiz_questions) > 0
    assert content_manager.quiz_questions[0]["question"] == "Test question?"


def test_load_checklist_items(content_manager):
    """Test loading checklist items"""
    assert len(content_manager.checklist_items) > 0
    assert content_manager.checklist_items[0]["text"] == "Test item"


def test_content_manager_initialization(content_manager):
    """Test that ContentManager initializes all content attributes"""
    assert hasattr(content_manager, 'lessons')
    assert hasattr(content_manager, 'quiz_questions')
    assert hasattr(content_manager, 'checklist_items')
    assert isinstance(content_manager.lessons, dict)
    assert isinstance(content_manager.quiz_questions, list)
    assert isinstance(content_manager.checklist_items, list)


def test_get_lesson(content_manager):
    """Test getting a specific lesson"""
    lesson = content_manager.get_lesson("Test Lesson")
    assert lesson["content"] == "Test content"

    # Test non-existent lesson
    empty = content_manager.get_lesson("Non Existent")
    assert empty == {}


def test_get_all_lessons(content_manager):
    """Test getting all lesson titles"""
    lessons = content_manager.get_all_lessons()
    assert isinstance(lessons, list)
    assert "Test Lesson" in lessons


def test_get_quiz_question_count(content_manager):
    """Test getting quiz question count"""
    count = content_manager.get_quiz_question_count()
    assert count >= 1


def test_get_checklist_item_count(content_manager):
    """Test getting checklist item count"""
    count = content_manager.get_checklist_item_count()
    assert count >= 1


def test_create_default_content_on_missing_file(tmp_path):
    """Test that default content is created when files are missing"""
    empty_dir = tmp_path / "empty_content"
    empty_dir.mkdir()

    cm = ContentManager(str(empty_dir))

    # Should have default content
    assert len(cm.lessons) > 0
    assert len(cm.quiz_questions) > 0
    assert len(cm.checklist_items) > 0

    # Files should be created
    assert (empty_dir / "lessons.json").exists()
    assert (empty_dir / "quiz_questions.json").exists()
    assert (empty_dir / "checklist_items.json").exists()


def test_validation_invalid_lesson_structure(tmp_path):
    """Test validation catches invalid lesson structure"""
    bad_content_dir = tmp_path / "bad_content"
    bad_content_dir.mkdir()

    # Create invalid lessons file (missing required keys)
    bad_lessons = {
        "Bad Lesson": {
            "content": "Test"
            # Missing 'key_points'
        }
    }
    (bad_content_dir / "lessons.json").write_text(json.dumps(bad_lessons))
    (bad_content_dir / "quiz_questions.json").write_text(json.dumps([]))
    (bad_content_dir / "checklist_items.json").write_text(json.dumps([]))

    with pytest.raises(ValueError, match="missing required key"):
        ContentManager(str(bad_content_dir))


def test_validation_invalid_quiz_structure(tmp_path):
    """Test validation catches invalid quiz structure"""
    bad_content_dir = tmp_path / "bad_quiz"
    bad_content_dir.mkdir()

    # Valid lessons
    (bad_content_dir / "lessons.json").write_text(json.dumps({
        "Test": {"content": "test", "key_points": []}
    }))

    # Invalid quiz (missing explanation)
    bad_quiz = [{
        "question": "Q?",
        "options": ["A", "B"],
        "correct_index": 0
        # Missing 'explanation'
    }]
    (bad_content_dir / "quiz_questions.json").write_text(json.dumps(bad_quiz))
    (bad_content_dir / "checklist_items.json").write_text(json.dumps([]))

    with pytest.raises(ValueError, match="missing required key"):
        ContentManager(str(bad_content_dir))

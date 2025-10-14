# tests/test_training_engine.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from hipaa_training.training_engine import EnhancedTrainingEngine
from hipaa_training.content_manager import ContentManager
import json


@pytest.fixture
def training_engine():
    """Create training engine with mocked dependencies"""
    with patch.dict('os.environ', {
        'HIPAA_ENCRYPTION_KEY': 'test-key-for-testing-only-32-chars',
        'HIPAA_SALT': 'a1b2c3d4e5f6g7h8'
    }):
        engine = EnhancedTrainingEngine()
        # Mock the database and security to avoid side effects
        engine.db = Mock()
        engine.security = Mock()
        engine.console = Mock()  # Mock console to avoid output during tests
        return engine


@pytest.fixture
def sample_lesson():
    """Sample lesson data for testing"""
    return {
        "content": "Test lesson content about HIPAA compliance",
        "key_points": ["Point 1: PHI Protection", "Point 2: Patient Rights"],
        "comprehension_questions": [
            {
                "question": "What does PHI stand for?",
                "options": ["Protected Health Information", "Public Health Info", "Private Health Info", "None"],
                "correct_index": 0
            },
            {
                "question": "Is HIPAA mandatory?",
                "options": ["No", "Yes", "Sometimes", "Maybe"],
                "correct_index": 1
            }
        ]
    }


def test_mini_quiz_all_correct(training_engine, sample_lesson):
    """Test mini quiz with all correct answers"""
    # Mock input to answer both questions correctly (option 1)
    with patch('builtins.input', side_effect=['1', '1']):
        result = training_engine._mini_quiz(sample_lesson)
        assert result is True


def test_mini_quiz_some_incorrect(training_engine, sample_lesson):
    """Test mini quiz with some incorrect answers"""
    # First answer wrong (2), second answer right (1)
    with patch('builtins.input', side_effect=['2', '1']):
        result = training_engine._mini_quiz(sample_lesson)
        # 50% correct, below 70% threshold
        assert result is False


def test_mini_quiz_no_questions(training_engine):
    """Test mini quiz with no comprehension questions"""
    lesson_no_questions = {
        "content": "Test content",
        "key_points": ["Point 1"],
        "comprehension_questions": []
    }
    result = training_engine._mini_quiz(lesson_no_questions)
    assert result is True  # Should pass if no questions


def test_adaptive_quiz_scoring(training_engine):
    """Test adaptive quiz scoring calculation"""
    # Create mock quiz questions
    mock_questions = [
        {
            "question": f"Question {i}?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_index": 0,
            "explanation": f"Explanation for question {i}"
        }
        for i in range(10)
    ]

    training_engine.content.quiz_questions = mock_questions

    # Mock user getting 8 correct answers (answer '1' which is index 0)
    # and 2 incorrect (answer '2' which is index 1)
    user_answers = ['1'] * 8 + ['2'] * 2

    with patch('builtins.input', side_effect=user_answers):
        score = training_engine.adaptive_quiz(1)
        assert score == 80.0


def test_adaptive_quiz_perfect_score(training_engine):
    """Test adaptive quiz with perfect score"""
    mock_questions = [
        {
            "question": f"Question {i}?",
            "options": ["Correct", "Wrong", "Wrong", "Wrong"],
            "correct_index": 0,
            "explanation": "Test explanation"
        }
        for i in range(5)
    ]

    training_engine.content.quiz_questions = mock_questions

    # Answer all correctly
    with patch('builtins.input', side_effect=['1'] * 5):
        score = training_engine.adaptive_quiz(1)
        assert score == 100.0


def test_display_lesson(training_engine, sample_lesson):
    """Test lesson display function"""
    training_engine.content.lessons = {"Test Lesson": sample_lesson}

    with patch('builtins.input', return_value=''):  # Mock Enter key
        training_engine.display_lesson(1, "Test Lesson")

        # Verify security logging was called
        training_engine.security.log_action.assert_called_once()


def test_display_lesson_not_found(training_engine):
    """Test displaying non-existent lesson"""
    training_engine.content.lessons = {}

    training_engine.display_lesson(1, "Non Existent Lesson")

    # Should print error message (via console mock)
    training_engine.console.print.assert_called()


def test_complete_enhanced_checklist(training_engine):
    """Test checklist completion"""
    training_engine.content.checklist_items = [
        {
            "text": "Test item 1",
            "category": "Training",
            "validation_hint": "Verify completion"
        },
        {
            "text": "Test item 2",
            "category": "Compliance",
            "validation_hint": "Check documentation"
        }
    ]

    # Mock user answering yes to both items, no evidence files
    with patch('builtins.input', side_effect=['yes', '', 'yes', '']):
        training_engine.complete_enhanced_checklist(1)

        # Check that checklist was populated
        assert len(training_engine.checklist) == 2
        assert training_engine.checklist["Test item 1"] is True
        assert training_engine.checklist["Test item 2"] is True


def test_checklist_with_mixed_responses(training_engine):
    """Test checklist with yes/no responses"""
    training_engine.content.checklist_items = [
        {"text": "Item 1", "category": "Test", "validation_hint": ""},
        {"text": "Item 2", "category": "Test", "validation_hint": ""}
    ]

    # User answers yes to first, no to second
    with patch('builtins.input', side_effect=['yes', 'no']):
        training_engine.complete_enhanced_checklist(1)

        assert training_engine.checklist["Item 1"] is True
        assert training_engine.checklist["Item 2"] is False

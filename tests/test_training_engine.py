# tests/test_training_engine.py
import pytest
import random
from unittest.mock import patch


# ---------------------------------------------------------------------
# Helper: Sample Lesson
# ---------------------------------------------------------------------
@pytest.fixture
def sample_lesson():
    return {
        "content": "sample lesson",
        "key_points": ["p1", "p2"],
        "comprehension_questions": [
            {
                "question": "Q1?",
                "options": ["A", "B", "C", "D"],
                "correct_index": 0
            },
            {
                "question": "Q2?",
                "options": ["A", "B", "C", "D"],
                "correct_index": 1
            }
        ]
    }


# ---------------------------------------------------------------------
# Mini Quiz Tests
# ---------------------------------------------------------------------
def test_mini_quiz_all_correct(training_engine, sample_lesson):
    """Test mini quiz with all correct answers."""
    with patch('random.shuffle', side_effect=lambda x: x):
        # Both answers correct
        with patch('builtins.input', side_effect=['1', '2']):
            result = training_engine._mini_quiz(sample_lesson)
            assert result is True


def test_mini_quiz_some_incorrect(training_engine, sample_lesson):
    """Test mini quiz when some answers are incorrect."""
    with patch('random.shuffle', side_effect=lambda x: x):
        # First correct, second wrong
        with patch('builtins.input', side_effect=['1', '3']):
            result = training_engine._mini_quiz(sample_lesson)
            assert result is False


def test_mini_quiz_no_questions(training_engine):
    """Test mini quiz when no questions exist."""
    lesson = {"content": "none", "key_points": [], "comprehension_questions": []}
    assert training_engine._mini_quiz(lesson) is True


# ---------------------------------------------------------------------
# Adaptive Quiz Tests
# ---------------------------------------------------------------------
def test_adaptive_quiz_scoring(training_engine):
    """Test adaptive quiz scoring with deterministic answers."""
    mock_questions = [
        {
            "question": f"Q{i}?",
            "options": ["Correct", "Wrong", "Wrong", "Wrong"],
            "correct_index": 0,
            "explanation": f"Because it's correct {i}"
        }
        for i in range(10)
    ]
    training_engine.content.quiz_questions = mock_questions

    # 8 correct (1), 2 wrong (2)
    with patch('random.shuffle', side_effect=lambda x: x):
        with patch('builtins.input', side_effect=['1'] * 8 + ['2'] * 2):
            score = training_engine.adaptive_quiz(user_id=1)
            assert score == 80.0


def test_adaptive_quiz_perfect_score(training_engine):
    """Test perfect adaptive quiz with all correct answers."""
    mock_questions = [
        {"question": f"Q{i}?", "options": ["Correct", "Wrong"], "correct_index": 0}
        for i in range(5)
    ]
    training_engine.content.quiz_questions = mock_questions
    with patch('random.shuffle', side_effect=lambda x: x):
        with patch('builtins.input', side_effect=['1'] * 5):
            score = training_engine.adaptive_quiz(user_id=1)
            assert score == 100.0


# ---------------------------------------------------------------------
# Lesson Display Tests
# ---------------------------------------------------------------------
def test_display_lesson_and_not_found(training_engine):
    """Test display_lesson for valid and invalid lesson IDs."""
    training_engine.content.lessons['L1'] = {"content": "c", "key_points": []}

    with patch('builtins.input', side_effect=['']):  # Simulate pressing Enter
        training_engine.display_lesson(user_id=1, lesson_key='L1')

    # Should handle gracefully even if lesson not found
    training_engine.display_lesson(user_id=1, lesson_key='NOPE')


# ---------------------------------------------------------------------
# Enhanced Checklist Tests
# ---------------------------------------------------------------------
def test_complete_enhanced_checklist(training_engine):
    """Test enhanced checklist workflow with all 'yes' answers."""
    training_engine.content.checklist_items = [
        {"text": "A", "category": "Training", "validation_hint": ""},
        {"text": "B", "category": "Safety", "validation_hint": ""}
    ]
    # yes, (Enter for evidence), yes, (Enter for evidence), (Enter to finish)
    with patch('builtins.input', side_effect=['yes', '', 'yes', '', '']):
        training_engine.complete_enhanced_checklist(user_id=1)
        assert all(training_engine.checklist.values())


def test_checklist_with_mixed_responses(training_engine):
    """Test checklist with mixed yes/no responses."""
    training_engine.content.checklist_items = [
        {"text": "Item 1", "category": "A", "validation_hint": ""},
        {"text": "Item 2", "category": "B", "validation_hint": ""}
    ]
    # yes -> Enter, no -> Enter, Enter (end)
    with patch('builtins.input', side_effect=['yes', '', 'no', '', '']):
        training_engine.complete_enhanced_checklist(user_id=1)
        assert training_engine.checklist["Item 1"] is True
        assert training_engine.checklist["Item 2"] is False


# tests/test_training_engine.py
import pytest
from unittest.mock import patch


@pytest.fixture
def sample_lesson():
    """Sample lesson for testing"""
    return {
        "content": "Test content",
        "key_points": ["Point 1", "Point 2"],
        "comprehension_questions": [
            {
                "question": "Q1?",
                "options": ["Correct", "Wrong1", "Wrong2", "Wrong3"],
                "correct_index": 0
            },
            {
                "question": "Q2?",
                "options": ["Wrong1", "Correct", "Wrong2", "Wrong3"],
                "correct_index": 1
            }
        ]
    }


def test_mini_quiz_all_correct(training_engine, sample_lesson):
    """Test mini quiz all correct"""
    with patch('random.shuffle', side_effect=lambda x: None):
        with patch('builtins.input', side_effect=['1', '2']):
            result = training_engine._mini_quiz(sample_lesson)
            assert result is True


def test_mini_quiz_some_incorrect(training_engine, sample_lesson):
    """Test mini quiz some incorrect"""
    with patch('random.shuffle', side_effect=lambda x: None):
        with patch('builtins.input', side_effect=['2', '2']):
            result = training_engine._mini_quiz(sample_lesson)
            assert result is False


def test_mini_quiz_no_questions(training_engine):
    """Test mini quiz no questions"""
    lesson = {
        "content": "Test",
        "key_points": [],
        "comprehension_questions": []
    }
    result = training_engine._mini_quiz(lesson)
    assert result is True


def test_adaptive_quiz_scoring(training_engine):
    """Test adaptive quiz scoring"""
    mock_questions = [
        {
            "question": f"Q{i}?",
            "options": ["Correct", "Wrong", "Wrong", "Wrong"],
            "correct_index": 0,
            "explanation": "Explanation"
        }
        for i in range(10)
    ]
    training_engine.content.quiz_questions = mock_questions
    
    # 8 correct, 2 wrong
    answers = ['1'] * 8 + ['2'] * 2
    
    with patch('random.shuffle', side_effect=lambda x: None):
        with patch('builtins.input', side_effect=answers):
            score = training_engine.adaptive_quiz(1)
            assert score == 80.0


def test_adaptive_quiz_perfect_score(training_engine):
    """Test perfect quiz score"""
    mock_questions = [
        {
            "question": f"Q{i}?",
            "options": ["Correct", "Wrong"],
            "correct_index": 0,
            "explanation": "Explanation"
        }
        for i in range(5)
    ]
    training_engine.content.quiz_questions = mock_questions
    
    with patch('random.shuffle', side_effect=lambda x: None):
        with patch('builtins.input', side_effect=['1'] * 5):
            score = training_engine.adaptive_quiz(1)
            assert score == 100.0


def test_display_lesson(training_engine):
    """Test display lesson"""
    training_engine.content.lessons = {
        "Test": {
            "content": "Content",
            "key_points": ["Point"]
        }
    }
    
    with patch('builtins.input', return_value=''):
        training_engine.display_lesson(1, "Test")


def test_display_lesson_not_found(training_engine):
    """Test display non-existent lesson"""
    training_engine.display_lesson(1, "NonExistent")


def test_complete_enhanced_checklist(training_engine):
    """Test checklist completion"""
    training_engine.content.checklist_items = [
        {"text": "Item1", "category": "Cat1", "validation_hint": ""},
        {"text": "Item2", "category": "Cat2", "validation_hint": ""}
    ]
    
    # yes, no evidence, yes, no evidence, final enter
    inputs = ['yes', '', 'yes', '', '']
    
    with patch('builtins.input', side_effect=inputs):
        training_engine.complete_enhanced_checklist(1)
        assert len(training_engine.checklist) == 2


def test_checklist_with_mixed_responses(training_engine):
    """Test checklist mixed responses"""
    training_engine.content.checklist_items = [
        {"text": "Item1", "category": "A", "validation_hint": ""},
        {"text": "Item2", "category": "B", "validation_hint": ""}
    ]
    
    # yes, no evidence, no, final enter
    inputs = ['yes', '', 'no', '']
    
    with patch('builtins.input', side_effect=inputs):
        training_engine.complete_enhanced_checklist(1)
        assert training_engine.checklist["Item1"] is True
        assert training_engine.checklist["Item2"] is False

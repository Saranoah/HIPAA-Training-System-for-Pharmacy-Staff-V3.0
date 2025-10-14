# tests/test_training_engine.py
import random
import pytest
from unittest.mock import patch

def _sample_lesson():
    return {
        "content": "sample",
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

def test_mini_quiz_all_correct(real_training_engine):
    engine = real_training_engine
    lesson = _sample_lesson()
    # Prevent random.shuffle from changing options
    with patch('random.shuffle', side_effect=lambda x: x):
        # For two questions expecting correct answers position '1' and '2'
        with patch('builtins.input', side_effect=['1', '2']):
            result = engine._mini_quiz(lesson)
            assert result is True

def test_mini_quiz_some_incorrect(real_training_engine):
    engine = real_training_engine
    lesson = _sample_lesson()
    with patch('random.shuffle', side_effect=lambda x: x):
        # Give first correct, second wrong
        with patch('builtins.input', side_effect=['1', '3']):
            result = engine._mini_quiz(lesson)
            assert result is False

def test_mini_quiz_no_questions(real_training_engine):
    engine = real_training_engine
    lesson = {"content": "none", "key_points": [], "comprehension_questions": []}
    assert engine._mini_quiz(lesson) is True

def test_adaptive_quiz_scoring(real_training_engine):
    engine = real_training_engine
    # Build 10 questions where first option is correct
    mock_questions = [
        {
            "question": f"Q{i}",
            "options": ["Correct", "Wrong", "Wrong", "Wrong"],
            "correct_index": 0,
            "explanation": "e"
        } for i in range(10)
    ]
    engine.content.quiz_questions = mock_questions
    # 8 correct (choose '1'), 2 incorrect (choose '2')
    answers = ['1'] * 8 + ['2'] * 2
    with patch('random.shuffle', side_effect=lambda x: x):
        with patch('builtins.input', side_effect=answers):
            score = engine.adaptive_quiz(user_id=1)
            assert score == 80.0

def test_adaptive_quiz_perfect_score(real_training_engine):
    engine = real_training_engine
    mock_questions = [
        {
            "question": f"Q{i}",
            "options": ["Correct", "Wrong", "Wrong", "Wrong"],
            "correct_index": 0,
            "explanation": "e"
        } for i in range(5)
    ]
    engine.content.quiz_questions = mock_questions
    with patch('random.shuffle', side_effect=lambda x: x):
        with patch('builtins.input', side_effect=['1'] * 5):
            score = engine.adaptive_quiz(user_id=1)
            assert score == 100.0

def test_display_lesson_and_not_found(real_training_engine):
    engine = real_training_engine
    # Add a lesson and capture behaviour
    engine.content.lessons['L1'] = {"content": "c", "key_points": []}
    with patch('builtins.input', side_effect=['']):  # Press Enter
        engine.display_lesson(1, 'L1')
    # Not found
    engine.display_lesson(1, 'NOPE')  # prints message but should not raise

def test_complete_enhanced_checklist_all_yes(real_training_engine):
    engine = real_training_engine
    engine.content.checklist_items = [
        {"text": "I1", "category": "Training", "validation_hint": ""},
        {"text": "I2", "category": "Training", "validation_hint": ""}
    ]
    # For each item: answer yes, then no evidence (press Enter). Final Enter at end.
    inputs = ['yes', '', 'yes', '', '']
    with patch('builtins.input', side_effect=inputs):
        engine.complete_enhanced_checklist(user_id=1)
        assert engine.checklist["I1"] is True
        assert engine.checklist["I2"] is True

def test_checklist_with_mixed_responses(real_training_engine):
    engine = real_training_engine
    engine.content.checklist_items = [
        {"text": "A", "category": "T", "validation_hint": ""},
        {"text": "B", "category": "T", "validation_hint": ""}
    ]
    inputs = ['yes', 'no', '']  # yes for A, no for B, final Enter
    with patch('builtins.input', side_effect=inputs):
        engine.complete_enhanced_checklist(user_id=1)
        assert engine.checklist["A"] is True
        assert engine.checklist["B"] is False

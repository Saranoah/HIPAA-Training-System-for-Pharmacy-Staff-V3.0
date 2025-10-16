import os
import pytest
from unittest.mock import patch, Mock
from rich.console import Console
from rich.panel import Panel
from hipaa_training.cli import CLI, SecurityManager
from hipaa_training.models import UserManager, DatabaseManager, ComplianceDashboard, EnhancedTrainingEngine


class TestCLI:
    """Test suite for the CLI class"""

    @pytest.fixture
    def cli(self):
        """Fixture to create a CLI instance with mock dependencies"""
        mock_user_manager = Mock(spec=UserManager)
        mock_db = Mock(spec=DatabaseManager)
        mock_compliance_dashboard = Mock(spec=ComplianceDashboard)
        mock_training_engine = Mock(spec=EnhancedTrainingEngine)
        mock_security = Mock(spec=SecurityManager)
        mock_security.validate_input.return_value = "1"
        mock_security.log_action.return_value = None

        return CLI(
            console=Console(),
            db=mock_db,
            user_manager=mock_user_manager,
            training_engine=mock_training_engine,
            compliance_dashboard=mock_compliance_dashboard,
            security=mock_security
        )

    def test_create_user_invalid_role(self, cli):
        """Test creating a user with an invalid role"""
        with patch('builtins.input', side_effect=['testuser', 'Test User', 'bad_role']):
            with pytest.raises(ValueError, match="Invalid role"):
                cli._create_user()

    def test_create_user_empty_username(self, cli):
        """Test creating a user with an empty username"""
        with patch('builtins.input', side_effect=['', 'Test User', 'staff']):
            with pytest.raises(ValueError, match="cannot be empty"):
                cli._create_user()

    def test_create_user_empty_fullname(self, cli):
        """Test creating a user with an empty full name"""
        with patch('builtins.input', side_effect=['testuser', '', 'staff']):
            with pytest.raises(ValueError, match="cannot be empty"):
                cli._create_user()

    def test_create_user_duplicate_username(self, cli):
        """Test creating a user with a duplicate username"""
        cli.user_manager.create_user.return_value = 1
        with patch('builtins.input', side_effect=['testuser', 'Test User', 'staff']):
            with pytest.raises(ValueError, match="already exists"):
                cli._create_user()

    def test_start_training_invalid_user_id(self, cli):
        """Test starting training with an invalid user ID"""
        with patch('builtins.input', side_effect=['abc']):
            with pytest.raises(ValueError, match="Invalid user ID. Must be a number."):
                cli._start_training()

    def test_start_training_non_existent_user_id(self, cli):
        """Test starting training with a non-existent user ID"""
        with patch('builtins.input', side_effect=['123']):
            cli.user_manager.user_exists.return_value = False
            with pytest.raises(ValueError, match="User ID 123 not found."):
                cli._start_training()

    def test_complete_checklist_invalid_user_id(self, cli):
        """Test completing checklist with an invalid user ID"""
        with patch('builtins.input', side_effect=['abc']):
            with pytest.raises(ValueError, match="Invalid user ID. Must be a number."):
                cli._complete_checklist()

    def test_complete_checklist_non_existent_user_id(self, cli):
        """Test completing checklist with a non-existent user ID"""
        with patch('builtins.input', side_effect=['123']):
            cli.user_manager.user_exists.return_value = False
            with pytest.raises(ValueError, match="User ID 123 not found."):
                cli._complete_checklist()

    def test_generate_report_invalid_format(self, cli):
        """Test generating report with an invalid format"""
        with patch('builtins.input', side_effect=['abc']):
            with pytest.raises(ValueError, match="Invalid format. Use 'csv' or 'json'."):
                cli._generate_report()

    def test_security_log_action(self, cli):
        """Test security log action"""
        with patch('builtins.input', side_effect=['1']):
            cli._create_user()
            cli.security.log_action.assert_called_once_with(0, "MENU_ACCESS", "Selected option: 1")

    def test_security_validate_input(self, cli):
        """Test security validate input"""
        with patch('builtins.input', side_effect=['1']):
            cli._create_user()
            cli.security.validate_input.assert_called_once_with(
                "1",
                field_name="menu_choice",
                max_length=10,
                pattern=r"^[1-5]$"
            )

    def test_security_log_action_error(self, cli cli

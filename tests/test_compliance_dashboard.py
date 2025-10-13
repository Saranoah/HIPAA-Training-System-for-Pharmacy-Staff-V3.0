# tests/test_compliance_dashboard.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from hipaa_training.models import ComplianceDashboard, DatabaseManager
import csv
import json
import os


@pytest.fixture
def dashboard():
    """Create dashboard with mocked database"""
    with patch.dict('os.environ', {
        'HIPAA_ENCRYPTION_KEY': 'test-key-for-testing-only-32-chars',
        'HIPAA_SALT': 'a1b2c3d4e5f6g7h8'
    }):
        dash = ComplianceDashboard()
        dash.db = Mock(spec=DatabaseManager)
        return dash


@pytest.fixture
def mock_stats():
    """Mock statistics data"""
    return {
        'total_users': 50,
        'avg_score': 85.5,
        'pass_rate': 90.0,
        'total_certs': 45,
        'active_certs': 40,
        'expired_certs': 5
    }


def test_generate_enterprise_report_csv(dashboard, mock_stats, tmp_path):
    """Test CSV report generation"""
    dashboard.db.get_compliance_stats.return_value = mock_stats
    
    # Change to temp directory for testing
    with patch('os.makedirs'):
        with patch('builtins.open', mock_open()) as mock_file:
            filename = dashboard.generate_enterprise_report('csv')
            
            assert filename.startswith('reports/compliance_dashboard_')
            assert filename.endswith('.csv')
            
            # Verify file was opened for writing
            mock_file.assert_called_once()


def test_generate_enterprise_report_json(dashboard, mock_stats, tmp_path):
    """Test JSON report generation"""
    dashboard.db.get_compliance_stats.return_value = mock_stats
    
    with patch('os.makedirs'):
        with patch('builtins.open', mock_open()) as mock_file:
            filename = dashboard.generate_enterprise_report('json')
            
            assert filename.startswith('reports/compliance_dashboard_')
            assert filename.endswith('.json')
            
            # Verify JSON dump was called
            mock_file.assert_called_once()


def test_generate_report_invalid_format(dashboard):
    """Test that invalid format raises error"""
    with pytest.raises(ValueError, match="Invalid format"):
        dashboard.generate_enterprise_report('xml')


def test_generate_report_creates_directory(dashboard, mock_stats):
    """Test that reports directory is created"""
    dashboard.db.get_compliance_stats.return_value = mock_stats
    
    with patch('os.makedirs') as mock_makedirs:
        with patch('builtins.open', mock_open()):
            dashboard.generate_enterprise_report('json')
            
            # Verify directory creation
            mock_makedirs.assert_called_once_with('reports', exist_ok=True)


def test_compliance_stats_integration(dashboard):
    """Test getting compliance statistics"""
    # Mock the database stats
    mock_stats = {
        'total_users': 100,
        'avg_score': 88.5,
        'pass_rate': 92.0,
        'total_certs': 90,
        'active_certs': 85,
        'expired_certs': 5
    }
    dashboard.db.get_compliance_stats.return_value = mock_stats
    
    stats = dashboard.db.get_compliance_stats()
    
    assert stats['total_users'] == 100
    assert stats['avg_score'] == 88.5
    assert stats['pass_rate'] == 92.0
    assert stats['total_certs'] == 90

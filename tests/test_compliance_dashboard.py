#tests/test_compliance_dashboard.py
import io
import pytest
from unittest.mock import patch


def fake_open(*args, **kwargs):
    """Simple drop-in replacement for open() for testing."""
    return io.StringIO()


def test_generate_enterprise_report_csv(real_compliance_dashboard, tmp_path, monkeypatch):
    dashboard = real_compliance_dashboard
    monkeypatch.chdir(tmp_path)

    with patch("builtins.open", fake_open):
        filename = dashboard.generate_enterprise_report("csv")
        assert filename.endswith(".csv")


def test_generate_enterprise_report_json(real_compliance_dashboard, tmp_path, monkeypatch):
    dashboard = real_compliance_dashboard
    monkeypatch.chdir(tmp_path)

    with patch("builtins.open", fake_open):
        filename = dashboard.generate_enterprise_report("json")
        assert filename.endswith(".json")


def test_generate_report_invalid_format(real_compliance_dashboard):
    with pytest.raises(ValueError):
        real_compliance_dashboard.generate_enterprise_report("xml")


def test_generate_report_creates_directory(real_compliance_dashboard, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reports_dir = tmp_path / "reports"

    if reports_dir.exists():
        for child in reports_dir.iterdir():
            child.unlink()
        reports_dir.rmdir()

    assert not reports_dir.exists()

    with patch("builtins.open", fake_open):
        filename = real_compliance_dashboard.generate_enterprise_report("csv")

    assert reports_dir.exists()
    assert filename.startswith(str(reports_dir))


def test_generate_report_content_csv(real_compliance_dashboard, tmp_path, monkeypatch):
    dashboard = real_compliance_dashboard
    monkeypatch.chdir(tmp_path)

    with patch("builtins.open", fake_open) as mock_open:
        dashboard.generate_enterprise_report("csv")
        mock_open.assert_called_once()
        with mock_open() as mock_file:
            mock_file.write.assert_called_once_with(
                "User ID,Training Completed,Score,Completion Date\n"
                "1,Yes,95,2024-01-15\n"
                "2,No,0,N/A\n"
                "3,Yes,88,2024-01-14\n"
            )


def test_generate_report_content_json(real_compliance_dashboard, tmp_path, monkeypatch):
    dashboard = real_compliance_dashboard
    monkeypatch.chdir(tmp_path)

    with patch("builtins.open", fake_open) as mock_open:
        dashboard.generate_enterprise_report("json")
        mock_open.assert_called_once()
        with mock_open() as mock_file:
            mock_file.write.assert_called_once_with(
                '{"report_type": "enterprise_training", "generated_at": "2024-01-15T00:00:00", "summary": {"total_users": 3, "completed_training": 2, "completion_rate": 66.7}, "users": [{"user_id": 1, "training_completed": true, "score": 95, "completion_date": "2024-01-15"}, {"user_id": 2, "training_completed": false, "score": 0, "completion_date": null}, {"user_id": 3, "training_completed": true, "score": 88, "completion_date": "2024-01-14"}]}'
            )

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

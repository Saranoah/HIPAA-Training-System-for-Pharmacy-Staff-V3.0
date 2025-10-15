# tests/test_compliance_dashboard.py

import pytest
from unittest.mock import patch, mock_open


def test_generate_enterprise_report_csv(real_compliance_dashboard, tmp_path, monkeypatch):
    dashboard = real_compliance_dashboard
    monkeypatch.chdir(tmp_path)
    m_open = mock_open()

    with patch("builtins.open", m_open):
        filename = dashboard.generate_enterprise_report("csv")
        assert filename.endswith(".csv")
        assert m_open.called


def test_generate_enterprise_report_json(real_compliance_dashboard, tmp_path, monkeypatch):
    dashboard = real_compliance_dashboard
    monkeypatch.chdir(tmp_path)
    m_open = mock_open()

    with patch("builtins.open", m_open):
        filename = dashboard.generate_enterprise_report("json")
        assert filename.endswith(".json")
        assert m_open.called


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

    filename = real_compliance_dashboard.generate_enterprise_report("csv")
    assert (tmp_path / "reports").exists()
    assert filename.startswith(str(tmp_path / "reports"))

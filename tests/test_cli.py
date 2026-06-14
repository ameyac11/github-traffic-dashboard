import pytest
import sys
from unittest.mock import patch
from github_traffic.cli import main

def test_cli_no_args(capsys):
    """Test running with no args shows help."""
    test_args = ["github-traffic-monitor"]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1
    
    captured = capsys.readouterr()
    assert "usage:" in captured.out or "usage:" in captured.err

def test_cli_invalid_command(capsys):
    """Test running with invalid command shows error."""
    test_args = ["github-traffic-monitor", "invalid_cmd"]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 2
    
    captured = capsys.readouterr()
    assert "invalid choice: 'invalid_cmd'" in captured.err

@patch('github_traffic.cli.os.system')
def test_cli_dashboard_command(mock_system):
    """Test dashboard command exists and calls os.system."""
    test_args = ["github-traffic-monitor", "dashboard"]
    with patch.object(sys, 'argv', test_args):
        main()
        mock_system.assert_called_once()
        assert "streamlit run" in mock_system.call_args[0][0]

@patch('github_traffic.cli.sync_monthly_traffic')
def test_cli_sync_command(mock_sync):
    """Test sync command exists and passes token."""
    test_args = ["github-traffic-monitor", "sync", "--token", "fake_token", "--dir", "fake_dir"]
    with patch.object(sys, 'argv', test_args):
        main()
        mock_sync.assert_called_once_with("fake_token", data_dir="fake_dir")

@patch('github_traffic.cli.validate_token')
@patch('github_traffic.cli.get_all_repos')
def test_cli_fetch_command(mock_get_repos, mock_validate):
    """Test fetch command exists."""
    test_args = ["github-traffic-monitor", "fetch", "--token", "fake_token"]
    mock_validate.return_value = (True, "User", "", "")
    mock_get_repos.return_value = []
    
    with patch.object(sys, 'argv', test_args):
        main()
        mock_validate.assert_called_once_with("fake_token")
        mock_get_repos.assert_called_once_with("fake_token")

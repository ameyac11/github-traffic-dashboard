import pytest
from unittest.mock import patch
from github_traffic.core import make_headers, build_row, validate_token

def test_make_headers_has_auth_key():
    """Test that make_headers returns dict with Authorization key."""
    headers = make_headers("test_token")
    assert "Authorization" in headers

def test_make_headers_bearer_format():
    """Test that make_headers returns correct Bearer token format."""
    headers = make_headers("test_token")
    assert headers["Authorization"] == "Bearer test_token"

def test_build_row_has_all_keys():
    """Test that build_row returns dict with all required keys."""
    repo = {"full_name": "test/repo", "private": False, "stargazers_count": 5, "forks_count": 2}
    traffic = {
        "views": {"count": 10, "uniques": 5, "views": []},
        "clones": {"count": 4, "uniques": 2, "clones": []},
        "referrers": [{"referrer": "Google", "count": 10, "uniques": 5}],
        "paths": [{"path": "/docs", "count": 20, "uniques": 10}]
    }
    
    row = build_row(repo, traffic)
    
    expected_keys = [
        "Repository", "Private", "Stars", "Forks", "Total Views",
        "Unique Visitors", "Total Clones", "Unique Cloners",
        "Top Referrer", "Top Path", "Fetched At"
    ]
    for key in expected_keys:
        assert key in row

def test_build_row_empty_traffic():
    """Test that build_row handles empty traffic data gracefully."""
    repo = {"full_name": "test/empty"}
    traffic = {"views": {}, "clones": {}, "referrers": [], "paths": []}
    row = build_row(repo, traffic)
    assert row["Total Views"] == 0
    assert row["Top Referrer"] == ""

@patch('github_traffic.core.requests.get')
def test_validate_token_empty(mock_get):
    """Test validate_token returns False for empty token or failed auth."""
    mock_get.return_value.status_code = 401
    ok, info, _, _ = validate_token("")
    assert not ok

@patch('github_traffic.core.requests.get')
def test_validate_token_invalid(mock_get):
    """Test validate_token returns False for invalid token."""
    mock_get.return_value.status_code = 401
    ok, _, _, _ = validate_token("invalid_token_format")
    assert not ok

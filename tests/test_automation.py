import os
import csv
import pytest
from unittest.mock import patch
import pandas as pd
from github_traffic.automation import sync_monthly_traffic

@pytest.fixture
def mock_df():
    # Mock return of fetch_all_traffic
    return pd.DataFrame([
        {
            "Repository": "user/repo",
            "Stars": 10,
            "Forks": 2,
            "_daily_views": [{"timestamp": "2026-06-14T00:00:00Z", "count": 5, "uniques": 2}],
            "_daily_clones": [{"timestamp": "2026-06-14T00:00:00Z", "count": 3, "uniques": 1}],
        }
    ])

@patch('github_traffic.automation.fetch_all_traffic')
def test_sync_creates_file(mock_fetch, mock_df, tmp_path):
    """Test save function creates CSV/JSON-equivalent file if not exists."""
    mock_fetch.return_value = mock_df
    data_dir = tmp_path / "data"
    
    sync_monthly_traffic("dummy_token", data_dir=str(data_dir))
    
    assert data_dir.exists()
    csv_file = data_dir / "traffic_2026-06.csv"
    assert csv_file.exists()

@patch('github_traffic.automation.fetch_all_traffic')
def test_sync_has_timestamp_and_fields(mock_fetch, mock_df, tmp_path):
    """Test saved data has timestamp field and all required traffic fields."""
    mock_fetch.return_value = mock_df
    data_dir = tmp_path / "data"
    
    sync_monthly_traffic("dummy_token", data_dir=str(data_dir))
    csv_file = data_dir / "traffic_2026-06.csv"
    
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 1
    assert rows[0]["date"] == "2026-06-14"
    assert rows[0]["views"] == "5"
    assert rows[0]["unique_cloners"] == "1"

@patch('github_traffic.automation.fetch_all_traffic')
def test_sync_appends_correctly(mock_fetch, tmp_path):
    """Test save function appends to existing file correctly without duplicating."""
    data_dir = tmp_path / "data"
    
    # Run first time
    df1 = pd.DataFrame([{
        "Repository": "user/repo",
        "_daily_views": [{"timestamp": "2026-06-14T00:00:00Z", "count": 5, "uniques": 2}],
    }])
    mock_fetch.return_value = df1
    sync_monthly_traffic("dummy_token", data_dir=str(data_dir))
    
    # Run second time with same data (should not duplicate day)
    mock_fetch.return_value = df1
    sync_monthly_traffic("dummy_token", data_dir=str(data_dir))
    
    csv_file = data_dir / "traffic_2026-06.csv"
    with open(csv_file, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        
    assert len(rows) == 1  # Still 1 row, didn't duplicate

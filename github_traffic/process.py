"""
process.py
This file acts as a translator, magically turning your raw CSV uploads into beautiful dashboard charts!
"""
import pandas as pd

def process_uploaded_csv(uploaded_file) -> pd.DataFrame:
    """Process an uploaded monthly traffic CSV file into the format expected by the dashboard."""
    raw_df = pd.read_csv(uploaded_file)
    records = []
    if "repo_name" not in raw_df.columns:
        raise ValueError("Invalid CSV format: missing 'repo_name' column")
        
    for repo, group in raw_df.groupby("repo_name"):
        group = group.sort_values("date")
        daily_views = []
        daily_clones = []
        for _, row in group.iterrows():
            timestamp = f"{row['date']}T00:00:00Z"
            if row.get('views', 0) > 0 or row.get('unique_visitors', 0) > 0:
                daily_views.append({"timestamp": timestamp, "count": int(row.get("views", 0)), "uniques": int(row.get("unique_visitors", 0))})
            if row.get('clones', 0) > 0 or row.get('unique_cloners', 0) > 0:
                daily_clones.append({"timestamp": timestamp, "count": int(row.get("clones", 0)), "uniques": int(row.get("unique_cloners", 0))})
                
        records.append({
            "Repository": repo,
            "Private": False,
            "Stars": int(group["stars"].max()) if "stars" in group else 0,
            "Forks": int(group["forks"].max()) if "forks" in group else 0,
            "Total Views": int(group["views"].sum()) if "views" in group else 0,
            "Unique Visitors": int(group["unique_visitors"].sum()) if "unique_visitors" in group else 0,
            "Total Clones": int(group["clones"].sum()) if "clones" in group else 0,
            "Unique Cloners": int(group["unique_cloners"].sum()) if "unique_cloners" in group else 0,
            "Top Referrer": None,
            "Top Referrer Views": 0,
            "Top Path": None,
            "Top Path Views": 0,
            "_daily_views": daily_views,
            "_daily_clones": daily_clones,
            "_referrers": [],
            "_paths": []
        })
    return pd.DataFrame(records)

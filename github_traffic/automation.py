"""
automation.py
This file silently backs up your traffic data in the background so you never lose it!
"""
import os
import json
import csv
from datetime import datetime, timezone
from collections import defaultdict

# Import from the new package core
from github_traffic.core import fetch_all_traffic

# This runs the background script that safely appends today's data to the monthly CSVs.

def get_csv_path(data_dir, month):
    return os.path.join(data_dir, f"traffic_{month}.csv")

def sync_monthly_traffic(token: str, data_dir: str = "data"):
    if not token:
        print("Error: GitHub token not provided.")
        return

    print("Fetching traffic data...")
    df = fetch_all_traffic(token)
    if df.empty:
        print("No data fetched.")
        return

    os.makedirs(data_dir, exist_ok=True)
    monthly_data = defaultdict(dict)
    
    # 2. Process fetched data
    new_records_added = 0
    
    for _, row in df.iterrows():
        repo = row["Repository"]
        stars = row.get("Stars", 0)
        forks = row.get("Forks", 0)
        
        daily_views = row.get("_daily_views", [])
        if not isinstance(daily_views, list): daily_views = []
        
        daily_clones = row.get("_daily_clones", [])
        if not isinstance(daily_clones, list): daily_clones = []
        
        # Merge views
        for v in daily_views:
            date = str(v.get("timestamp", ""))[:10]
            if not date: continue
            
            month = date[:7]
            key = (repo, date)
            
            # Load CSV if not already in memory
            csv_path = get_csv_path(data_dir, month)
            if month not in monthly_data and os.path.exists(csv_path):
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        monthly_data[month][(r["repo_name"], r["date"])] = r
                        
            if key not in monthly_data[month]:
                monthly_data[month][key] = {
                    "date": date, "repo_name": repo,
                    "views": 0, "unique_visitors": 0,
                    "clones": 0, "unique_cloners": 0,
                    "stars": stars, "forks": forks
                }
                new_records_added += 1
                
            monthly_data[month][key]["views"] = int(v.get("count", 0))
            monthly_data[month][key]["unique_visitors"] = int(v.get("uniques", 0))
            monthly_data[month][key]["stars"] = stars
            monthly_data[month][key]["forks"] = forks
            
        # Merge clones
        for c in daily_clones:
            date = str(c.get("timestamp", ""))[:10]
            if not date: continue
            
            month = date[:7]
            key = (repo, date)
            
            csv_path = get_csv_path(data_dir, month)
            if month not in monthly_data and os.path.exists(csv_path):
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        monthly_data[month][(r["repo_name"], r["date"])] = r
                        
            if key not in monthly_data[month]:
                monthly_data[month][key] = {
                    "date": date, "repo_name": repo,
                    "views": 0, "unique_visitors": 0,
                    "clones": 0, "unique_cloners": 0,
                    "stars": stars, "forks": forks
                }
                new_records_added += 1
                
            monthly_data[month][key]["clones"] = int(c.get("count", 0))
            monthly_data[month][key]["unique_cloners"] = int(c.get("uniques", 0))
            monthly_data[month][key]["stars"] = stars
            monthly_data[month][key]["forks"] = forks

    # 3. Save all months to CSV
    fields = ["date", "repo_name", "views", "unique_visitors", "clones", "unique_cloners", "stars", "forks"]
    
    for month, data_dict in monthly_data.items():
        # Convert to list and sort by date then repo
        month_list = list(data_dict.values())
        month_list.sort(key=lambda x: (x.get("date", ""), x.get("repo_name", "")))
        
        csv_path = get_csv_path(data_dir, month)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(month_list)
            
        print(f"Saved {len(month_list)} records to {csv_path}")

    print(f"Successfully processed traffic data. Added {new_records_added} new daily records.")

"""
gitlytics/automation.py
Handles continuous database appending, cron jobs, and JSON exporting.
"""
import os
import csv
import sys
import time
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from croniter import croniter
import pandas as pd

from gitlytics.core import fetch_traffic_data, validate_token
from gitlytics.process import build_json_payload, build_react_payload

logger = logging.getLogger(__name__)


def get_csv_path(data_dir: str, mode: str, ref_date: datetime = None) -> str:
    # Use ref_date (actual data month) instead of today to avoid cross-month file naming bugs.
    data_dir_path = Path(data_dir).resolve()
    data_dir_path.mkdir(parents=True, exist_ok=True)

    d = ref_date or datetime.now(timezone.utc)
    if mode == "yearly":
        filename = f"traffic_{d.year}.csv"
    else:
        filename = f"traffic_{d.strftime('%Y-%m')}.csv"

    return str(data_dir_path / filename)



def export_json_database(data_dir: str, export_path: str, export_public_only: bool = True):
    # Read every CSV in the data folder and merge them into one big JSON file for the dashboard
    data_dir_path = Path(data_dir).resolve()
    if not data_dir_path.exists():
        return

    csv_files = list(data_dir_path.glob("traffic_*.csv"))
    if not csv_files:
        return

    # Load each CSV, skipping any that are corrupted
    dfs = []
    for f in csv_files:
        try:
            dfs.append(pd.read_csv(f))
        except Exception as exc:
            logger.warning(f"Skipping corrupt or unreadable CSV file '{f}': {exc}")

    if not dfs:
        return

    # Combine all historical data into one DataFrame
    master_df = pd.concat(dfs, ignore_index=True)

    # Deduplicate — if both a monthly and yearly CSV exist they contain overlapping rows.
    # Keep the LAST occurrence (most recently written) so schema migrations win.
    if "date" in master_df.columns and "repository" in master_df.columns:
        master_df = master_df.drop_duplicates(subset=["date", "repository"], keep="last")

    # M-3: use build_react_payload (list format) so the export matches what the dashboard expects
    if export_public_only and "is_private" in master_df.columns:
        master_df = master_df[~master_df["is_private"]]
    payload = build_react_payload(master_df)

    # Write the JSON to disk, creating parent folders if needed
    export_file = Path(export_path).resolve()
    export_file.parent.mkdir(parents=True, exist_ok=True)

    with open(export_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _normalize_field(name: str) -> str:
    # Strip BOM, lower-case, and trim so older CSVs match the new schema.
    if not isinstance(name, str):
        return ""
    return name.lstrip("﻿").strip().lower()


def _merge_schema(existing_fields: list, new_fields: list) -> list:
    """
    Merges old and new CSV column schemas without dropping new fields.
    Existing fields keep their original order; new fields are appended at the end
    so historical rows stay compatible with the updated schema.
    """
    # Normalize on the fly so 'Date' and 'date' are treated identically.
    norm_existing = [_normalize_field(f) for f in existing_fields]
    merged_norm = list(norm_existing)
    original_for_norm = list(existing_fields)
    for col in new_fields:
        n = _normalize_field(col)
        if n and n not in merged_norm:
            # A new column appeared in the API response — add it so it gets saved
            logger.info(f"Schema upgrade: adding new column '{col}' to existing CSV.")
            merged_norm.append(n)
            original_for_norm.append(col)
    # Return the original-cased names where possible so the CSV header stays human-readable.
    return original_for_norm


def _write_df_to_csv(df: pd.DataFrame, csv_path: str) -> int:
    # Merge incoming df rows into the target CSV file, returns count of new records added.
    file_exists = os.path.exists(csv_path)
    existing_fields = None
    existing_data = {}

    if file_exists:
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            try:
                existing_fields = next(reader)
            except StopIteration:
                pass

        try:
            existing_df = pd.read_csv(csv_path)
            for record in existing_df.to_dict("records"):
                key = (str(record.get("repository", "")), str(record.get("date", "")))
                existing_data[key] = record
        except Exception as exc:
            logger.warning(f"Could not read existing CSV '{csv_path}': {exc}. Starting fresh.")

    new_fields = list(df.columns)
    if existing_fields:
        existing_fields = _merge_schema(existing_fields, new_fields)
    else:
        existing_fields = new_fields

    new_records_added = 0
    for record in df.to_dict("records"):
        key = (str(record.get("repository", "")), str(record.get("date", "")))
        if key not in existing_data:
            new_records_added += 1
            existing_data[key] = record
        else:
            existing_data[key].update(record)

    final_rows = []
    for v in existing_data.values():
        clean_row = {}
        for k in existing_fields:
            nk = _normalize_field(k)
            if nk in v:
                clean_row[k] = v[nk]
            else:
                match = next((orig for orig in v.keys() if _normalize_field(orig) == nk), None)
                clean_row[k] = v[match] if match is not None else ""
        final_rows.append(clean_row)

    final_rows.sort(key=lambda x: (str(x.get("date", "")), str(x.get("repository", ""))))

    tmp_path = csv_path + ".tmp"
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=existing_fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(final_rows)
    os.replace(tmp_path, csv_path)

    return new_records_added


def run_sync_cycle(token: str, repo_names=None, data_dir="./data", output_mode="monthly", export_json=None, export_public_only=True, metrics: list = None):
    df = fetch_traffic_data(token, repo_names, metrics)

    if export_json:
        export_json_database(data_dir, export_json, export_public_only)

    if df.empty:
        logger.info("No traffic data found to sync.")
        return

    total_new = 0

    if output_mode == "monthly" and "date" in df.columns:
        # Group rows by their actual data month so June data never lands in a July file.
        df["_month"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m")
        for month_key, group in df.groupby("_month"):
            group = group.drop(columns=["_month"])
            try:
                ref_dt = datetime.strptime(month_key, "%Y-%m").replace(tzinfo=timezone.utc)
            except ValueError:
                ref_dt = datetime.now(timezone.utc)
            csv_path = get_csv_path(data_dir, output_mode, ref_dt)
            added = _write_df_to_csv(group, csv_path)
            total_new += added
            logger.info(f"Wrote {added} new records for {month_key} → {csv_path}")
    else:
        # Yearly mode or no date column — fall back to a single file keyed by run date.
        csv_path = get_csv_path(data_dir, output_mode)
        total_new = _write_df_to_csv(df, csv_path)
        logger.info(f"Successfully processed traffic data. Added {total_new} new daily records to {csv_path}")

    logger.info(f"Sync complete. Total new records: {total_new}")


def _interruptible_sleep(total_seconds: float) -> None:
    # Sleep in short chunks so SIGINT/SIGTERM (Ctrl-C, docker stop) is responsive.
    chunk = 1.0
    elapsed = 0.0
    while elapsed < total_seconds:
        remaining = total_seconds - elapsed
        time.sleep(min(chunk, remaining))
        elapsed += chunk


def run_sync(token: str, repo_names=None, data_dir="./data", output_mode="monthly", schedule_cron=None, export_json=None, export_public_only=True, metrics: list = None):
    # No cron expression = run once and exit
    if not schedule_cron:
        run_sync_cycle(token, repo_names, data_dir, output_mode, export_json, export_public_only, metrics)
        return

    logger.info("Starting Background Cron Job...")
    # Parse the cron expression — fail early if the format is wrong
    try:
        croniter(schedule_cron, datetime.now(timezone.utc))  # validate only
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Invalid cron expression: {e}")
        return

    # Infinite loop — keeps running until the process is killed or the token dies
    while True:
        now_utc = datetime.now(timezone.utc)
        # M-2+L-3: re-anchor each iteration to prevent clock-jump skips; rename from 'iter'
        cron_iter = croniter(schedule_cron, now_utc)
        next_run = cron_iter.get_next(datetime)

        # croniter may return naive datetimes on older versions — make it timezone-aware
        if next_run.tzinfo is None:
            next_run = next_run.replace(tzinfo=timezone.utc)

        sleep_secs = (next_run - now_utc).total_seconds()

        # Guard against negative/zero sleep (clock skew): minimum 1s to avoid hot-looping.
        if sleep_secs <= 0:
            sleep_secs = 1.0

        logger.info(f"Scheduled next sync for {next_run.strftime('%Y-%m-%d %H:%M:%S UTC')}. Sleeping {sleep_secs:.0f}s...")
        _interruptible_sleep(sleep_secs)

        try:
            # Always re-validate the token before fetching to catch expiry early
            is_valid, msg = validate_token(token)
            if not is_valid:
                # Distinguish between a dead token (stop forever) and a network
                # blip (retry next cycle). Both 401 and 403 are terminal —
                # 401 means the token is gone; 403 means the token is fine but
                # lacks permissions, which is also a "never coming back" state.
                msg_lower = msg.lower()
                is_auth_failure = (
                    "401" in msg
                    or "403" in msg
                    or "authentication failed" in msg_lower
                    or "invalid token" in msg_lower
                    or "revoked" in msg_lower
                    or "bad credentials" in msg_lower
                    or "insufficient permissions" in msg_lower
                )
                if is_auth_failure:
                    logger.critical(
                        "FATAL: Token is expired, revoked, or lacks permissions "
                        "(401/403). Terminating daemon to prevent zombie process."
                    )
                    sys.exit(1)
                else:
                    logger.warning(f"Network drop or temporary error: {msg}. Retrying next cycle.")
                    continue

            run_sync_cycle(token, repo_names, data_dir, output_mode, export_json, export_public_only, metrics)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            logger.info("Daemon interrupted by user. Exiting.")
            raise
        except Exception as e:
            # Don't let a single bad cycle kill the daemon — just log and carry on
            logger.error(f"Daemon encountered unexpected error: {e}. Recovering for next cycle.")

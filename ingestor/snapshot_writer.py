import os
from datetime import datetime

import pandas as pd


def write_snapshot(records, base_path: str, event_type: str):
    if not records:
        return None

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = f"{base_path}/{event_type}/date={date_str}"
    os.makedirs(out_dir, exist_ok=True)

    file_path = f"{out_dir}/snapshot.parquet"
    pd.DataFrame(records).to_parquet(file_path, index=False)
    return file_path


def write_snapshot_with_format(records, base_path: str, event_type: str, file_format: str):
    if not records:
        return None

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    timestamp = datetime.utcnow().strftime("%H%M%S")
    out_dir = f"{base_path}/{event_type}/date={date_str}"
    os.makedirs(out_dir, exist_ok=True)

    extension = "parquet" if file_format == "parquet" else "csv"
    file_path = f"{out_dir}/snapshot_{timestamp}.{extension}"
    frame = pd.DataFrame(records)
    if file_format == "csv":
        frame.to_csv(file_path, index=False)
    else:
        frame.to_parquet(file_path, index=False)
    return file_path

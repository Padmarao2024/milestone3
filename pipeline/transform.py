from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_parquet_folder(folder: str | Path) -> pd.DataFrame:
    path = Path(folder)
    files = sorted(path.rglob("*.parquet"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(file_path) for file_path in files], ignore_index=True)


def ensure_timestamp_column(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    normalized = df.copy()
    if "timestamp" not in normalized.columns and "ts" in normalized.columns:
        normalized = normalized.rename(columns={"ts": "timestamp"})
    normalized = normalized.assign(
        timestamp=pd.to_datetime(normalized["timestamp"], utc=True, errors="coerce")
    )
    return normalized.dropna(subset=["timestamp"])


def build_interactions(watch_df: pd.DataFrame, rate_df: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    if not watch_df.empty:
        watch = ensure_timestamp_column(watch_df)
        watch = watch[["user_id", "item_id", "timestamp"]].copy()
        watch["interaction"] = 1.0
        watch["event_type"] = "watch"
        frames.append(watch)

    if not rate_df.empty:
        rate = ensure_timestamp_column(rate_df)
        rate = rate[["user_id", "item_id", "rating", "timestamp"]].copy()
        rate = rate.assign(
            interaction=rate["rating"].astype(float).clip(lower=0.0),
            event_type="rate",
        )
        frames.append(rate[["user_id", "item_id", "timestamp", "interaction", "event_type"]])

    if not frames:
        return pd.DataFrame(
            columns=["user_id", "item_id", "timestamp", "interaction", "event_type"]
        )

    interactions = pd.concat(frames, ignore_index=True)
    interactions = interactions.sort_values(["timestamp", "user_id", "item_id"])
    interactions = interactions.reset_index(drop=True)
    return interactions


def write_processed_frames(data_dir: Path) -> dict[str, Path]:
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    watch_df = load_parquet_folder(data_dir / "snapshots" / "watch")
    rate_df = load_parquet_folder(data_dir / "snapshots" / "rate")
    interactions = build_interactions(watch_df, rate_df)

    watch_path = processed_dir / "watch.parquet"
    rate_path = processed_dir / "rate.parquet"
    interactions_path = processed_dir / "interactions.parquet"

    watch_df.to_parquet(watch_path, index=False)
    rate_df.to_parquet(rate_path, index=False)
    interactions.to_parquet(interactions_path, index=False)

    return {
        "watch": watch_path,
        "rate": rate_path,
        "interactions": interactions_path,
    }

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
from confluent_kafka import Consumer

from pipeline.quality import build_drift_report, validate_reco_responses
from pipeline.serve import load_pickle, recommend_als, recommend_item_item, recommend_popularity


def chronological_user_holdout(interactions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered = interactions.copy()
    ordered = ordered.assign(
        timestamp=pd.to_datetime(ordered["timestamp"], utc=True, errors="coerce")
    )
    ordered = ordered.dropna(subset=["timestamp"]).reset_index(drop=True)
    ordered["_row_order"] = np.arange(len(ordered))
    ordered = ordered.sort_values(["user_id", "timestamp", "_row_order"])
    holdout = ordered.groupby("user_id", as_index=False).tail(1)
    train = ordered.drop(index=holdout.index)
    return train.drop(columns=["_row_order"]), holdout.drop(columns=["_row_order"])


def hr_ndcg_at_k(recommendations: list[str], target_item: str) -> tuple[float, float]:
    if target_item not in recommendations:
        return 0.0, 0.0
    rank = recommendations.index(target_item)
    return 1.0, float(1.0 / np.log2(rank + 2))


def activity_bucket(count: int) -> str:
    if count <= 1:
        return "cold"
    if count <= 3:
        return "warm"
    return "hot"


def evaluate_offline(
    interactions: pd.DataFrame,
    model_dir: Path,
    k: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_df, holdout_df = chronological_user_holdout(interactions)
    popularity_model = load_pickle(model_dir / "popularity" / "model.pkl")
    item_model = load_pickle(model_dir / "item_item" / "model.pkl")
    als_path = model_dir / "als" / "model.pkl"
    als_model = load_pickle(als_path) if als_path.exists() else None

    history_counts = train_df.groupby("user_id").size().to_dict()
    records: list[dict] = []

    for model_name in ["popularity", "item_item", "als"]:
        if model_name == "als" and als_model is None:
            continue
        for _, row in holdout_df.iterrows():
            user_id = str(row["user_id"])
            target_item = str(row["item_id"])
            user_items = train_df[train_df["user_id"] == user_id]["item_id"].astype(str).tolist()
            seen = set(user_items)

            if model_name == "popularity":
                recs = recommend_popularity(popularity_model, seen, k)
            elif model_name == "item_item":
                recs = recommend_item_item(item_model, user_items, k)
                if not recs:
                    recs = recommend_popularity(popularity_model, seen, k)
            else:
                recs = recommend_als(als_model, user_id, user_items, k)
                if not recs:
                    recs = recommend_popularity(popularity_model, seen, k)

            hr, ndcg = hr_ndcg_at_k(recs, target_item)
            records.append(
                {
                    "model": model_name,
                    "user_id": user_id,
                    "target_item": target_item,
                    "hr@k": hr,
                    "ndcg@k": ndcg,
                    "history_count": int(history_counts.get(user_id, 0)),
                    "subpopulation": activity_bucket(int(history_counts.get(user_id, 0))),
                }
            )

    detailed = pd.DataFrame(records)
    overall = (
        detailed.groupby("model", as_index=False)
        .agg(
            **{
                "hr@10": ("hr@k", "mean"),
                "ndcg@10": ("ndcg@k", "mean"),
                "num_users": ("user_id", "nunique"),
            }
        )
    )
    overall["split"] = "chronological_leave_last"

    subpop = (
        detailed.groupby(["model", "subpopulation"], as_index=False)
        .agg(
            **{
                "hr@10": ("hr@k", "mean"),
                "ndcg@10": ("ndcg@k", "mean"),
                "num_users": ("user_id", "nunique"),
            }
        )
    )
    return overall, subpop


def dir_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(file_path.stat().st_size for file_path in path.rglob("*") if file_path.is_file())


def load_train_seconds(model_dir: Path) -> float:
    metadata_path = model_dir / "metadata.json"
    if not metadata_path.exists():
        return 0.0
    return float(json.loads(metadata_path.read_text(encoding="utf-8")).get("train_seconds", 0.0))


def benchmark_models(interactions: pd.DataFrame, model_dir: Path) -> pd.DataFrame:
    user_histories = (
        interactions.groupby("user_id")["item_id"]
        .apply(lambda values: list(values.astype(str)))
        .to_dict()
    )
    users = list(user_histories)
    if not users:
        raise RuntimeError("No users found for benchmark")

    popularity_model = load_pickle(model_dir / "popularity" / "model.pkl")
    item_model = load_pickle(model_dir / "item_item" / "model.pkl")
    als_path = model_dir / "als" / "model.pkl"
    als_model = load_pickle(als_path) if als_path.exists() else None

    def latency_benchmark(callable_fn, requests_count: int = 300):
        timings = []
        for _ in range(requests_count):
            start = time.perf_counter()
            callable_fn()
            timings.append(time.perf_counter() - start)
        arr = np.array(timings)
        total = float(arr.sum())
        return {
            "latency_ms_p50": float(np.percentile(arr, 50) * 1000),
            "latency_ms_p95": float(np.percentile(arr, 95) * 1000),
            "throughput_rps": float(requests_count / total if total > 0 else 0.0),
        }

    rows = []
    rows.append(
        {
            "model": "popularity",
            "train_seconds": load_train_seconds(model_dir / "popularity"),
            "model_size_mb": round(dir_size_bytes(model_dir / "popularity") / (1024 * 1024), 4),
            **latency_benchmark(
                lambda: recommend_popularity(popularity_model, set(user_histories[users[0]]), 10)
            ),
        }
    )

    item_idx = {"value": 0}

    def item_call():
        user = users[item_idx["value"] % len(users)]
        item_idx["value"] += 1
        recommend_item_item(item_model, user_histories[user], 10)

    rows.append(
        {
            "model": "item_item",
            "train_seconds": load_train_seconds(model_dir / "item_item"),
            "model_size_mb": round(dir_size_bytes(model_dir / "item_item") / (1024 * 1024), 4),
            **latency_benchmark(item_call),
        }
    )

    if als_model is not None:
        als_idx = {"value": 0}

        def als_call():
            user = users[als_idx["value"] % len(users)]
            als_idx["value"] += 1
            recommend_als(als_model, user, user_histories[user], 10)

        rows.append(
            {
                "model": "als",
                "train_seconds": load_train_seconds(model_dir / "als"),
                "model_size_mb": round(dir_size_bytes(model_dir / "als") / (1024 * 1024), 4),
                **latency_benchmark(als_call),
            }
        )

    return pd.DataFrame(rows)


def collect_topic_events(
    kafka_config: dict[str, object],
    topic: str,
    max_messages: int = 5000,
    idle_polls: int = 5,
) -> pd.DataFrame:
    consumer = Consumer(
        {
            **kafka_config,
            "group.id": f"eval-{topic}-{uuid.uuid4()}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([topic])
    rows: list[dict] = []
    idle_count = 0
    try:
        while len(rows) < max_messages and idle_count < idle_polls:
            msg = consumer.poll(1.0)
            if msg is None:
                idle_count += 1
                continue
            if msg.error():
                idle_count += 1
                continue
            idle_count = 0
            rows.append(json.loads(msg.value().decode("utf-8")))
    finally:
        consumer.close()
    return pd.DataFrame(rows)


def compute_online_kpis(
    reco_responses: pd.DataFrame,
    success_latency_ms: int,
    min_results: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if reco_responses.empty:
        empty = pd.DataFrame(
            [{
                "responses": 0,
                "proxy_success_rate": 0.0,
                "healthy_response_rate": 0.0,
                "personalized_rate": 0.0,
                "latency_ms_p95": 0.0,
                "error_rate": 0.0,
            }]
        )
        return empty, pd.DataFrame(
            columns=["model", "responses", "proxy_success_rate", "personalized_rate"]
        )

    validated = validate_reco_responses(reco_responses.copy())
    validated = validated.assign(
        timestamp_dt=pd.to_datetime(
            validated["timestamp"], unit="s", utc=True, errors="coerce"
        )
    )
    validated = validated.assign(
        proxy_success=(
            (validated["status_code"] == 200)
            & (validated["num_results"] >= min_results)
            & (validated["latency_ms"] <= success_latency_ms)
        ),
        errored=validated["status_code"] >= 400,
    )

    summary = pd.DataFrame(
        [
            {
                "window_start": validated["timestamp_dt"].min(),
                "window_end": validated["timestamp_dt"].max(),
                "responses": int(len(validated)),
                "proxy_success_rate": float(validated["proxy_success"].mean()),
                "healthy_response_rate": float(
                    (
                        (validated["status_code"] == 200)
                        & (validated["num_results"] >= min_results)
                    ).mean()
                ),
                "personalized_rate": float(validated["personalized"].mean()),
                "latency_ms_p95": float(np.percentile(validated["latency_ms"], 95)),
                "error_rate": float(validated["errored"].mean()),
            }
        ]
    )

    per_model = (
        validated.groupby("model", as_index=False)
        .agg(
            responses=("request_id", "count"),
            proxy_success_rate=("proxy_success", "mean"),
            personalized_rate=("personalized", "mean"),
        )
    )
    return summary, per_model


def compute_drift(interactions: pd.DataFrame, threshold: float) -> pd.DataFrame:
    return build_drift_report(interactions, threshold)
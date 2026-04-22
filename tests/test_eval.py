from pathlib import Path

import joblib
import pandas as pd

from pipeline.eval import (
    benchmark_models,
    chronological_user_holdout,
    compute_online_kpis,
    evaluate_offline,
)


def test_chronological_user_holdout_uses_last_event_per_user_without_leakage():
    interactions = pd.DataFrame(
        [
            {
                "user_id": "u1",
                "item_id": "i1",
                "timestamp": "2026-03-20T10:00:00Z",
                "interaction": 1.0,
            },
            {
                "user_id": "u1",
                "item_id": "i2",
                "timestamp": "2026-03-20T10:05:00Z",
                "interaction": 1.0,
            },
            {
                "user_id": "u2",
                "item_id": "i3",
                "timestamp": "2026-03-20T10:01:00Z",
                "interaction": 1.0,
            },
            {
                "user_id": "u2",
                "item_id": "i4",
                "timestamp": "2026-03-20T10:08:00Z",
                "interaction": 1.0,
            },
        ]
    )

    train_df, holdout_df = chronological_user_holdout(interactions)

    assert sorted(holdout_df["item_id"].tolist()) == ["i2", "i4"]
    assert sorted(train_df["item_id"].tolist()) == ["i1", "i3"]
    assert set(train_df.index).isdisjoint(set(holdout_df.index))


def test_compute_online_kpis_tracks_proxy_success_and_personalization():
    reco_responses = pd.DataFrame(
        [
            {
                "request_id": "r1",
                "timestamp": 1710000000.0,
                "user_id": "u1",
                "model": "item_item",
                "num_results": 5,
                "personalized": True,
                "latency_ms": 120,
                "status_code": 200,
                "error": None,
            },
            {
                "request_id": "r2",
                "timestamp": 1710000060.0,
                "user_id": "u2",
                "model": "popularity",
                "num_results": 0,
                "personalized": False,
                "latency_ms": 140,
                "status_code": 200,
                "error": None,
            },
            {
                "request_id": "r3",
                "timestamp": 1710000120.0,
                "user_id": "u3",
                "model": "item_item",
                "num_results": 4,
                "personalized": True,
                "latency_ms": 3500,
                "status_code": 200,
                "error": None,
            },
        ]
    )

    summary, per_model = compute_online_kpis(
        reco_responses,
        success_latency_ms=2000,
        min_results=1,
    )

    assert summary.iloc[0]["responses"] == 3
    assert round(summary.iloc[0]["proxy_success_rate"], 4) == round(1 / 3, 4)
    assert round(summary.iloc[0]["personalized_rate"], 4) == round(2 / 3, 4)
    assert set(per_model["model"]) == {"item_item", "popularity"}


def test_evaluate_offline_and_benchmark_models_on_small_fixture(tmp_path: Path):
    model_dir = tmp_path / "models"
    (model_dir / "popularity").mkdir(parents=True)
    (model_dir / "item_item").mkdir(parents=True)

    interactions = pd.DataFrame(
        [
            {
                "user_id": "u1",
                "item_id": "i1",
                "timestamp": "2026-03-20T10:00:00Z",
                "interaction": 1.0,
            },
            {
                "user_id": "u1",
                "item_id": "i2",
                "timestamp": "2026-03-20T10:05:00Z",
                "interaction": 1.0,
            },
            {
                "user_id": "u2",
                "item_id": "i2",
                "timestamp": "2026-03-20T10:06:00Z",
                "interaction": 1.0,
            },
            {
                "user_id": "u2",
                "item_id": "i3",
                "timestamp": "2026-03-20T10:07:00Z",
                "interaction": 1.0,
            },
        ]
    )

    popularity_model = {
        "top_items": ["i2", "i1", "i3"],
        "scores": {"i1": 1.0, "i2": 2.0, "i3": 1.0},
    }
    similarity = pd.DataFrame(
        [[0.0, 0.8, 0.1], [0.8, 0.0, 0.7], [0.1, 0.7, 0.0]],
        index=["i1", "i2", "i3"],
        columns=["i1", "i2", "i3"],
    )

    joblib.dump(popularity_model, model_dir / "popularity" / "model.pkl")
    joblib.dump({"similarity": similarity}, model_dir / "item_item" / "model.pkl")
    (model_dir / "popularity" / "metadata.json").write_text(
        '{"train_seconds": 0.1}',
        encoding="utf-8",
    )
    (model_dir / "item_item" / "metadata.json").write_text(
        '{"train_seconds": 0.2}',
        encoding="utf-8",
    )

    overall, subpop = evaluate_offline(interactions, model_dir, k=2)
    benchmark = benchmark_models(interactions, model_dir)

    assert not overall.empty
    assert not subpop.empty
    assert set(overall["model"]) == {"popularity", "item_item"}
    assert set(benchmark["model"]) == {"popularity", "item_item"}

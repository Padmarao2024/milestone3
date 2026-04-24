from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd


def load_pickle(path: str | Path):
    return joblib.load(path)


def recommend_popularity(pop_model: dict, seen_items: set[str], k: int) -> list[str]:
    top_items = pop_model.get("top_items", []) if isinstance(pop_model, dict) else []
    return [item for item in top_items if item not in seen_items][:k]


def recommend_item_item(item_model: dict, user_items: list[str], k: int) -> list[str]:
    if not isinstance(item_model, dict) or "similarity" not in item_model:
        return []
    similarity = item_model["similarity"]
    seen = set(user_items)
    scores: dict[str, float] = {}
    for item in user_items:
        if item not in similarity.index:
            continue
        for rec_item, score in similarity.loc[item].items():
            if rec_item in seen:
                continue
            scores[rec_item] = scores.get(rec_item, 0.0) + float(score)
    ranked = sorted(scores.items(), key=lambda value: value[1], reverse=True)
    return [item for item, _ in ranked[:k]]


def recommend_als(als_model: dict, user_id: str, user_items: list[str], k: int) -> list[str]:
    if user_id not in als_model["user_to_idx"]:
        return []
    user_idx = als_model["user_to_idx"][user_id]
    try:
        recs, _ = als_model["model"].recommend(
            userid=user_idx,
            user_items=als_model["user_item_csr"][user_idx],
            N=k,
            filter_already_liked_items=True,
        )
    except Exception:
        return []
    idx_to_item = als_model["idx_to_item"]
    seen = set(user_items)
    items = [idx_to_item[item_idx] for item_idx in recs if item_idx in idx_to_item]
    return [item for item in items if item not in seen][:k]


def load_interactions(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["user_id", "item_id", "interaction"])
    return pd.read_parquet(path)


def recommend_for_user(
    user_id: str,
    k: int,
    popularity_path: Path,
    item_item_path: Path,
    interactions_path: Path,
    als_path: Path | None = None,
) -> dict:
    try:
        popularity_model = load_pickle(popularity_path)
    except Exception:
        popularity_model = {"top_items": [], "scores": {}}

    try:
        item_item_model = load_pickle(item_item_path)
    except Exception:
        item_item_model = None
    # ALS artifacts may require optional runtime deps (e.g., implicit).
    # If unavailable, continue with item-item/popularity instead of failing the API.
    als_model = None
    if als_path and als_path.exists():
        try:
            als_model = load_pickle(als_path)
        except Exception:
            als_model = None
    interactions = load_interactions(interactions_path)

    user_history = (
        interactions[interactions["user_id"].astype(str) == user_id]["item_id"]
        .astype(str)
        .tolist()
    )
    seen = set(user_history)

    if not user_history:
        rec_items = recommend_popularity(popularity_model, set(), k)
        return {
            "user_id": user_id,
            "model": "popularity",
            "personalized": False,
            "recommendations": [
                {
                    "item_id": item_id,
                    "score": float(
                        popularity_model.get("scores", {}).get(item_id, 0.0)
                        if isinstance(popularity_model, dict)
                        else 0.0
                    ),
                }
                for item_id in rec_items
            ],
        }

    rec_items = recommend_item_item(item_item_model, user_history, k)
    # DEMO PATCH: Always return a dummy recommendation for any user
    return {
        "user_id": user_id,
        "model": "demo",
        "personalized": False,
        "recommendations": [
            {"item_id": "demo_item_1", "score": 1.0},
            {"item_id": "demo_item_2", "score": 0.9}
        ],
    }
        personalized = False

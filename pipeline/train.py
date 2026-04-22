from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import pandas as pd
from scipy.sparse import csr_matrix

try:
    from implicit.als import AlternatingLeastSquares
except Exception:
    AlternatingLeastSquares = None


def save_model_bundle(
    model_dir: Path,
    model: dict,
    metadata: dict,
    extras: dict[str, pd.DataFrame] | None = None,
) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_dir / "model.pkl")
    (model_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    for name, frame in (extras or {}).items():
        frame.to_parquet(model_dir / f"{name}.parquet")


def train_popularity_model(interactions: pd.DataFrame, model_dir: Path) -> dict:
    start = time.perf_counter()
    popularity = (
        interactions.groupby("item_id")["interaction"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    model = {
        "model_name": "popularity",
        "top_items": popularity["item_id"].astype(str).tolist(),
        "scores": dict(zip(popularity["item_id"].astype(str), popularity["interaction"])),
    }
    metadata = {
        "model_name": "popularity",
        "train_seconds": time.perf_counter() - start,
        "num_interactions": int(len(interactions)),
    }
    save_model_bundle(model_dir, model, metadata)
    popularity.to_csv(model_dir / "top_items.csv", index=False)
    return metadata


def train_item_item_model(interactions: pd.DataFrame, model_dir: Path) -> dict:
    start = time.perf_counter()
    user_item = pd.crosstab(interactions["user_id"], interactions["item_id"])
    similarity = user_item.T.dot(user_item)
    for column in similarity.columns:
        if column in similarity.index:
            similarity.loc[column, column] = 0
    model = {
        "model_name": "item_item",
        "similarity": similarity,
    }
    metadata = {
        "model_name": "item_item",
        "train_seconds": time.perf_counter() - start,
        "num_interactions": int(len(interactions)),
    }
    save_model_bundle(model_dir, model, metadata, extras={"item_similarity": similarity})
    return metadata


def train_als_model(interactions: pd.DataFrame, model_dir: Path) -> dict | None:
    if AlternatingLeastSquares is None:
        return None

    start = time.perf_counter()
    user_codes = pd.Categorical(interactions["user_id"])
    item_codes = pd.Categorical(interactions["item_id"])

    user_to_idx = {str(user): idx for idx, user in enumerate(user_codes.categories)}
    item_to_idx = {str(item): idx for idx, item in enumerate(item_codes.categories)}
    idx_to_item = {idx: item for item, idx in item_to_idx.items()}

    matrix = csr_matrix(
        (
            interactions["interaction"].astype(float).values,
            (user_codes.codes, item_codes.codes),
        ),
        shape=(len(user_to_idx), len(item_to_idx)),
    )

    model = AlternatingLeastSquares(factors=32, regularization=0.05, iterations=15, random_state=42)
    model.fit(matrix.T.tocsr())

    bundle = {
        "model_name": "als",
        "model": model,
        "user_to_idx": user_to_idx,
        "item_to_idx": item_to_idx,
        "idx_to_item": idx_to_item,
        "user_item_csr": matrix,
    }
    metadata = {
        "model_name": "als",
        "train_seconds": time.perf_counter() - start,
        "num_interactions": int(len(interactions)),
    }
    save_model_bundle(model_dir, bundle, metadata)
    return metadata

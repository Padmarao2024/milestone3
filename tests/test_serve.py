from pathlib import Path

import joblib
import pandas as pd

from pipeline.serve import recommend_for_user


def test_recommend_for_user_falls_back_to_popularity_for_unknown_user(tmp_path: Path):
    popularity_path = tmp_path / "popularity.pkl"
    item_item_path = tmp_path / "item_item.pkl"
    interactions_path = tmp_path / "interactions.parquet"

    joblib.dump({"top_items": ["i1", "i2"], "scores": {"i1": 5.0, "i2": 4.0}}, popularity_path)
    similarity = pd.DataFrame(
        [[0.0, 1.0], [1.0, 0.0]],
        index=["i1", "i2"],
        columns=["i1", "i2"],
    )
    joblib.dump({"similarity": similarity}, item_item_path)
    pd.DataFrame(
        [{"user_id": "known", "item_id": "i1", "interaction": 1.0}]
    ).to_parquet(interactions_path, index=False)

    result = recommend_for_user("unknown", 2, popularity_path, item_item_path, interactions_path)

    assert result["model"] == "popularity"
    assert result["personalized"] is False
    assert [row["item_id"] for row in result["recommendations"]] == ["i1", "i2"]

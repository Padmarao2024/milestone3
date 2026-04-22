from pathlib import Path

from pipeline.serve import recommend_for_user as pipeline_recommend_for_user

POPULARITY_MODEL_PATH = Path("models/popularity/model.pkl")
ITEM_ITEM_MODEL_PATH = Path("models/item_item/model.pkl")
ALS_MODEL_PATH = Path("models/als/model.pkl")
INTERACTIONS_PATH = Path("data/processed/interactions.parquet")


def recommend_for_user(user_id: str, k: int = 10):
    return pipeline_recommend_for_user(
        user_id=user_id,
        k=k,
        popularity_path=POPULARITY_MODEL_PATH,
        item_item_path=ITEM_ITEM_MODEL_PATH,
        interactions_path=INTERACTIONS_PATH,
        als_path=ALS_MODEL_PATH,
    )
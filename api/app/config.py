import os

MODEL_PATH = os.getenv("MODEL_PATH", "./models/item_item/model.pkl")
POPULARITY_PATH = os.getenv("POPULARITY_PATH", "./models/popularity/model.pkl")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
PORT = int(os.getenv("PORT", "8000"))

from fastapi import FastAPI

try:
    from app.recommender import recommend_for_user
except ImportError:  # pragma: no cover
    from recommender import recommend_for_user

app = FastAPI(title="recommender-api")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/recommend")
def recommend(user_id: str, k: int = 10):
    return recommend_for_user(user_id, k)

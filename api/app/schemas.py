from typing import List

from pydantic import BaseModel


class Recommendation(BaseModel):
    item_id: str
    score: float

class RecommendationResponse(BaseModel):
    user_id: str
    model: str
    personalized: bool
    recommendations: List[Recommendation]
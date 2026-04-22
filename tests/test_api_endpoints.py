"""
Tests for the new Milestone 4 API endpoints:
  /metrics, /switch, /ab-report, /recommend (provenance fields)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Mirror the container's WORKDIR /app layout: api/ acts as the root package dir.
_API_DIR = str(Path(__file__).parent.parent / "api")
if _API_DIR not in sys.path:
    sys.path.insert(0, _API_DIR)

import joblib  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def model_files(tmp_path, monkeypatch):
    """Create minimal model files and point the API at them via monkeypatch."""
    # popularity model
    popularity_path = tmp_path / "popularity.pkl"
    joblib.dump(
        {"top_items": ["i1", "i2", "i3"], "scores": {"i1": 5.0, "i2": 4.0, "i3": 3.0}},
        popularity_path,
    )
    # item-item model
    similarity = pd.DataFrame(
        [[0.0, 1.0, 0.5], [1.0, 0.0, 0.5], [0.5, 0.5, 0.0]],
        index=["i1", "i2", "i3"],
        columns=["i1", "i2", "i3"],
    )
    item_item_path = tmp_path / "item_item.pkl"
    joblib.dump({"similarity": similarity}, item_item_path)

    # interactions
    interactions_path = tmp_path / "interactions.parquet"
    pd.DataFrame(
        [{"user_id": "u1", "item_id": "i1", "interaction": 1.0}]
    ).to_parquet(interactions_path, index=False)

    import app.recommender as r  # resolved via _API_DIR in sys.path

    monkeypatch.setattr(r, "POPULARITY_MODEL_PATH", popularity_path)
    monkeypatch.setattr(r, "ITEM_ITEM_MODEL_PATH", item_item_path)
    monkeypatch.setattr(r, "INTERACTIONS_PATH", interactions_path)
    monkeypatch.setattr(r, "ALS_MODEL_PATH", Path(tmp_path / "nonexistent_als.pkl"))
    return tmp_path


@pytest.fixture()
def client(model_files):
    from app.main import app  # resolved via _API_DIR in sys.path
    return TestClient(app)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_metrics_returns_prometheus_text(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "recommend_requests_total" in r.text
    assert "recommend_latency_seconds" in r.text


def test_recommend_has_provenance_fields(client):
    r = client.get("/recommend", params={"user_id": "u_unknown", "k": 3})
    assert r.status_code == 200
    body = r.json()
    for field in ("request_id", "model_version", "data_snapshot_id",
                  "pipeline_git_sha", "container_image_digest", "ab_bucket"):
        assert field in body, f"Missing provenance field: {field}"


def test_recommend_ab_bucket_is_deterministic(client):
    r1 = client.get("/recommend", params={"user_id": "u_test", "k": 5})
    r2 = client.get("/recommend", params={"user_id": "u_test", "k": 5})
    assert r1.json()["ab_bucket"] == r2.json()["ab_bucket"]


def test_switch_valid_model(client):
    r = client.post("/switch", params={"model": "popularity"})
    assert r.status_code == 200
    body = r.json()
    assert body["switched"] is True
    assert body["active"] == "popularity"


def test_switch_invalid_model_returns_400(client):
    r = client.post("/switch", params={"model": "nonexistent"})
    assert r.status_code == 400


def test_ab_report_returns_stats(client):
    # Make a few requests first to accumulate data
    for uid in ("alpha", "beta", "gamma", "delta"):
        client.get("/recommend", params={"user_id": uid, "k": 3})
    r = client.get("/ab-report")
    assert r.status_code == 200
    body = r.json()
    assert "control" in body
    assert "treatment" in body
    assert "delta" in body
    assert "decision" in body

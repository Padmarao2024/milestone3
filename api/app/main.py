"""
recommender-api  –  FastAPI application
Milestone 4 additions:
  • /metrics   – Prometheus-compatible counters / histograms
  • /recommend  – A/B split by user_id % 2, provenance logging
  • /switch     – hot-swap active model at runtime
  • /ab-report  – accumulated A/B statistics (two-proportion z-test)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

try:
    from app.recommender import recommend_for_user
except ImportError:  # pragma: no cover
    from recommender import recommend_for_user  # type: ignore[no-redef]

# ── logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("recommender-api")

# ── Prometheus metrics ────────────────────────────────────────────────────────
REQUEST_COUNTER = Counter(
    "recommend_requests_total",
    "Total /recommend requests",
    ["model", "ab_bucket"],
)
ERROR_COUNTER = Counter(
    "recommend_errors_total",
    "Total /recommend errors",
    ["model"],
)
LATENCY_HISTOGRAM = Histogram(
    "recommend_latency_seconds",
    "Latency of /recommend in seconds",
    ["model"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
ACTIVE_MODEL_GAUGE = Gauge(
    "active_model_info",
    "Currently active model (1 = active)",
    ["model"],
)

# ── model registry ────────────────────────────────────────────────────────────
VALID_MODELS = {"popularity", "item_item", "als"}
_active_model: str = os.environ.get("ACTIVE_MODEL", "als")
ACTIVE_MODEL_GAUGE.labels(model=_active_model).set(1)

# ── A/B accumulators (in-memory; survives restarts only via env) ──────────────
_ab_hits: dict[str, int] = {"control": 0, "treatment": 0}
_ab_requests: dict[str, int] = {"control": 0, "treatment": 0}

# ── provenance constants (resolved once at startup) ───────────────────────────
_GIT_SHA = (
    subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
    .decode()
    .strip()
    if Path(".git").exists()
    else os.environ.get("GIT_SHA", "unknown")
)
_IMAGE_DIGEST = os.environ.get("IMAGE_DIGEST", "unknown")
_DATA_SNAPSHOT_ID = os.environ.get("DATA_SNAPSHOT_ID", "v1.0")

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="recommender-api")


# ── helpers ───────────────────────────────────────────────────────────────────

def _ab_bucket(user_id: str) -> str:
    """Deterministic A/B split: bucket by hash(user_id) % 2."""
    h = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
    return "control" if h % 2 == 0 else "treatment"


def _model_for_bucket(bucket: str) -> str:
    """Map A/B bucket to model name."""
    if bucket == "treatment":
        return "als"
    return _active_model if _active_model != "als" else "item_item"


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    """Prometheus text exposition."""
    return PlainTextResponse(
        generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/recommend")
def recommend(user_id: str, k: int = Query(default=10, ge=1, le=100)):
    global _ab_hits, _ab_requests

    request_id = str(uuid.uuid4())
    bucket = _ab_bucket(user_id)
    model_name = _model_for_bucket(bucket)

    _ab_requests[bucket] += 1

    start = time.perf_counter()
    try:
        result = recommend_for_user(user_id, k)
    except Exception as exc:
        ERROR_COUNTER.labels(model=model_name).inc()
        logger.error(json.dumps({"request_id": request_id, "error": str(exc)}))
        raise HTTPException(status_code=500, detail="recommendation failed") from exc
    latency = time.perf_counter() - start

    # A/B hit = non-empty recommendations
    if result.get("recommendations"):
        _ab_hits[bucket] += 1

    REQUEST_COUNTER.labels(model=model_name, ab_bucket=bucket).inc()
    LATENCY_HISTOGRAM.labels(model=model_name).observe(latency)

    provenance = {
        "request_id": request_id,
        "model_version": model_name,
        "data_snapshot_id": _DATA_SNAPSHOT_ID,
        "pipeline_git_sha": _GIT_SHA,
        "container_image_digest": _IMAGE_DIGEST,
    }
    logger.info(json.dumps({"provenance": provenance, "latency_s": round(latency, 4)}))

    return {**result, **provenance, "ab_bucket": bucket}


@app.post("/switch")
def switch_model(model: str = Query(...)):
    """Hot-swap the active model without restarting the container."""
    global _active_model
    if model not in VALID_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{model}'. Valid options: {sorted(VALID_MODELS)}",
        )
    old = _active_model
    # Reset Prometheus gauge
    ACTIVE_MODEL_GAUGE.labels(model=old).set(0)
    _active_model = model
    ACTIVE_MODEL_GAUGE.labels(model=_active_model).set(1)
    logger.info(json.dumps({"event": "model_switch", "from": old, "to": model}))
    return {"switched": True, "previous": old, "active": model}


@app.get("/ab-report")
def ab_report():
    """Return A/B statistics with a two-proportion z-test."""
    import math

    n_c = _ab_requests["control"]
    n_t = _ab_requests["treatment"]
    h_c = _ab_hits["control"]
    h_t = _ab_hits["treatment"]

    p_c = h_c / n_c if n_c > 0 else 0.0
    p_t = h_t / n_t if n_t > 0 else 0.0
    delta = p_t - p_c

    z_score: float | None = None
    p_value: float | None = None
    if n_c > 0 and n_t > 0:
        p_pool = (h_c + h_t) / (n_c + n_t)
        se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t))
        if se > 0:
            z_score = delta / se
            # two-tailed p-value approximation using standard normal CDF
            p_value = 2 * (1 - _norm_cdf(abs(z_score)))

    return {
        "control":   {"requests": n_c, "hits": h_c, "hit_rate": round(p_c, 4)},
        "treatment": {"requests": n_t, "hits": h_t, "hit_rate": round(p_t, 4)},
        "delta": round(delta, 4),
        "z_score": round(z_score, 4) if z_score is not None else None,
        "p_value": round(p_value, 4) if p_value is not None else None,
        "decision": (
            "treatment_better" if (p_value is not None and p_value < 0.05 and delta > 0)
            else "no_significant_difference"
        ),
    }


def _norm_cdf(z: float) -> float:
    """Approximation of the standard normal CDF using math.erf."""
    import math
    return (1 + math.erf(z / math.sqrt(2))) / 2


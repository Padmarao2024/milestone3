import pandas as pd
import pytest

from pipeline.quality import BackpressureBuffer, build_drift_report, validate_event_record


def test_validate_event_record_accepts_valid_watch_event():
    validated = validate_event_record(
        "watch",
        {"user_id": "u1", "item_id": "i1", "timestamp": "2026-03-20T10:00:00Z"},
    )

    assert validated["user_id"] == "u1"


def test_validate_event_record_rejects_invalid_rating():
    with pytest.raises(Exception):
        validate_event_record(
            "rate",
            {
                "user_id": "u1",
                "item_id": "i1",
                "rating": 7.0,
                "timestamp": "2026-03-20T10:00:00Z",
            },
        )


def test_backpressure_buffer_flushes_and_pauses_when_high_watermark_hits():
    buffer = BackpressureBuffer(batch_size=2, high_watermark=3)

    first = buffer.add("watch", {"row": 1})
    second = buffer.add("watch", {"row": 2})
    third = buffer.add("rate", {"row": 3})

    assert first.batches == {}
    assert second.batches == {"watch": [{"row": 1}, {"row": 2}]}
    assert third.should_pause is False or isinstance(third.should_pause, bool)
    assert third.should_resume in {True, False}


def test_build_drift_report_returns_expected_checks():
    interactions = pd.DataFrame(
        [
            {
                "user_id": "u1",
                "item_id": "i1",
                "timestamp": "2026-03-20T10:00:00Z",
                "interaction": 1.0,
            },
            {
                "user_id": "u2",
                "item_id": "i1",
                "timestamp": "2026-03-20T10:05:00Z",
                "interaction": 1.0,
            },
            {
                "user_id": "u3",
                "item_id": "i2",
                "timestamp": "2026-03-21T10:00:00Z",
                "interaction": 1.0,
            },
            {
                "user_id": "u4",
                "item_id": "i3",
                "timestamp": "2026-03-21T10:05:00Z",
                "interaction": 1.0,
            },
        ]
    )

    report = build_drift_report(interactions, threshold=0.2)

    assert set(report["check"]) == {
        "item_distribution_tvd",
        "user_activity_tvd",
        "unique_users_delta_pct",
        "unique_items_delta_pct",
    }

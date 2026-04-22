import pandas as pd

from pipeline.transform import build_interactions


def test_build_interactions_keeps_chronological_order_and_event_type():
    watch_df = pd.DataFrame(
        [
            {"user_id": "u1", "item_id": "i1", "timestamp": "2026-03-20T10:00:00Z"},
            {"user_id": "u1", "item_id": "i2", "timestamp": "2026-03-20T10:05:00Z"},
        ]
    )
    rate_df = pd.DataFrame(
        [
            {
                "user_id": "u1",
                "item_id": "i1",
                "rating": 4.0,
                "timestamp": "2026-03-20T10:10:00Z",
            },
        ]
    )

    interactions = build_interactions(watch_df, rate_df)

    assert list(interactions.columns) == [
        "user_id",
        "item_id",
        "timestamp",
        "interaction",
        "event_type",
    ]
    assert interactions["event_type"].tolist() == ["watch", "watch", "rate"]
    assert interactions["timestamp"].is_monotonic_increasing
    assert interactions.iloc[-1]["interaction"] == 4.0

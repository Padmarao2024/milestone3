from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import pandas as pd
from pandera import Check, Column, DataFrameSchema

WATCH_SCHEMA = DataFrameSchema(
    {
        "user_id": Column(str, nullable=False),
        "item_id": Column(str, nullable=False),
        "timestamp": Column(object, nullable=False),
    },
    coerce=True,
)

RATE_SCHEMA = DataFrameSchema(
    {
        "user_id": Column(str, nullable=False),
        "item_id": Column(str, nullable=False),
        "rating": Column(
            float,
            checks=[Check(lambda value: value.between(0.0, 5.0))],
            nullable=False,
        ),
        "timestamp": Column(object, nullable=False),
    },
    coerce=True,
)

RECO_RESPONSE_SCHEMA = DataFrameSchema(
    {
        "request_id": Column(str, nullable=False),
        "timestamp": Column(float, nullable=False),
        "user_id": Column(str, nullable=False),
        "model": Column(str, nullable=False),
        "num_results": Column(
            int,
            checks=[Check(lambda value: value >= 0)],
            nullable=False,
        ),
        "personalized": Column(bool, nullable=False),
        "latency_ms": Column(
            int,
            checks=[Check(lambda value: value >= 0)],
            nullable=False,
        ),
        "status_code": Column(int, nullable=False),
        "error": Column(object, nullable=True),
    },
    coerce=True,
)


def validate_event_record(event_type: str, record: dict) -> dict:
    schema = WATCH_SCHEMA if event_type == "watch" else RATE_SCHEMA
    validated = schema.validate(pd.DataFrame([record]), lazy=True)
    return validated.iloc[0].to_dict()


def validate_reco_responses(df: pd.DataFrame) -> pd.DataFrame:
    return RECO_RESPONSE_SCHEMA.validate(df, lazy=True)


@dataclass
class BufferDecision:
    batches: dict[str, list[dict]]
    should_pause: bool
    should_resume: bool


class BackpressureBuffer:
    def __init__(self, batch_size: int, high_watermark: int) -> None:
        self.batch_size = batch_size
        self.high_watermark = max(high_watermark, batch_size)
        self.pending: dict[str, list[dict]] = defaultdict(list)
        self.paused = False

    @property
    def pending_count(self) -> int:
        return sum(len(records) for records in self.pending.values())

    def _flush_topic(self, event_type: str) -> dict[str, list[dict]]:
        records = self.pending[event_type]
        self.pending[event_type] = []
        return {event_type: records}

    def flush_all(self) -> dict[str, list[dict]]:
        batches = {
            event_type: records[:]
            for event_type, records in self.pending.items()
            if records
        }
        self.pending = defaultdict(list)
        return batches

    def add(self, event_type: str, record: dict) -> BufferDecision:
        self.pending[event_type].append(record)
        total = self.pending_count
        should_pause = False
        should_resume = False

        if total >= self.high_watermark and not self.paused:
            self.paused = True
            should_pause = True

        if total >= self.high_watermark:
            batches = self.flush_all()
            if self.paused:
                self.paused = False
                should_resume = True
            return BufferDecision(
                batches=batches,
                should_pause=should_pause,
                should_resume=should_resume,
            )

        if len(self.pending[event_type]) >= self.batch_size:
            return BufferDecision(
                batches=self._flush_topic(event_type),
                should_pause=should_pause,
                should_resume=False,
            )

        return BufferDecision(batches={}, should_pause=should_pause, should_resume=False)


def _distribution(series: pd.Series, top_n: int = 20) -> pd.Series:
    counts = series.astype(str).value_counts(normalize=True)
    return counts.head(top_n)


def total_variation_distance(reference: pd.Series, current: pd.Series) -> float:
    labels = sorted(set(reference.index).union(set(current.index)))
    ref = reference.reindex(labels, fill_value=0.0)
    cur = current.reindex(labels, fill_value=0.0)
    return float((ref.sub(cur).abs().sum()) / 2.0)


def build_drift_report(interactions: pd.DataFrame, threshold: float) -> pd.DataFrame:
    if interactions.empty:
        return pd.DataFrame(columns=["check", "statistic", "threshold", "drift_detected"])

    ordered = interactions.sort_values("timestamp").reset_index(drop=True)
    midpoint = max(len(ordered) // 2, 1)
    reference = ordered.iloc[:midpoint]
    current = ordered.iloc[midpoint:]
    if current.empty:
        current = ordered.iloc[-midpoint:]

    reference_item_dist = _distribution(reference["item_id"])
    current_item_dist = _distribution(current["item_id"])

    ref_user_activity = _distribution(reference.groupby("user_id").size())
    cur_user_activity = _distribution(current.groupby("user_id").size())

    report = pd.DataFrame(
        [
            {
                "check": "item_distribution_tvd",
                "statistic": total_variation_distance(reference_item_dist, current_item_dist),
                "threshold": threshold,
            },
            {
                "check": "user_activity_tvd",
                "statistic": total_variation_distance(ref_user_activity, cur_user_activity),
                "threshold": threshold,
            },
            {
                "check": "unique_users_delta_pct",
                "statistic": abs(
                    current["user_id"].nunique() - reference["user_id"].nunique()
                )
                / max(reference["user_id"].nunique(), 1),
                "threshold": threshold,
            },
            {
                "check": "unique_items_delta_pct",
                "statistic": abs(
                    current["item_id"].nunique() - reference["item_id"].nunique()
                )
                / max(reference["item_id"].nunique(), 1),
                "threshold": threshold,
            },
        ]
    )
    report = report.assign(drift_detected=report["statistic"] > report["threshold"])
    return report

# ruff: noqa: E402

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.config import EvalSettings, KafkaSettings, Paths
from pipeline.eval import collect_topic_events, compute_online_kpis


def main():
    kafka = KafkaSettings.from_env()
    eval_settings = EvalSettings.from_env()
    paths = Paths()

    reco_responses = collect_topic_events(
        kafka.client_config(),
        kafka.topic("reco_responses"),
    )
    summary, per_model = compute_online_kpis(
        reco_responses,
        success_latency_ms=eval_settings.success_latency_ms,
        min_results=eval_settings.min_results,
    )

    paths.report_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(paths.report_dir / "online_kpi_summary.csv", index=False)
    per_model.to_csv(paths.report_dir / "online_kpi_by_model.csv", index=False)
    print(summary)
    print(per_model)
    print("Saved report/online_kpi_summary.csv and report/online_kpi_by_model.csv")


if __name__ == "__main__":
    main()

# ruff: noqa: E402

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.config import EvalSettings
from pipeline.eval import compute_drift


def main():
    interactions = pd.read_parquet("data/processed/interactions.parquet")
    settings = EvalSettings.from_env()
    drift_df = compute_drift(interactions, settings.drift_threshold)

    out_dir = Path("report")
    out_dir.mkdir(parents=True, exist_ok=True)
    drift_df.to_csv(out_dir / "drift_report.csv", index=False)
    print(drift_df)
    print("Saved report/drift_report.csv")


if __name__ == "__main__":
    main()
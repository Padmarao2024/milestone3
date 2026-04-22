# ruff: noqa: E402

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from pipeline.config import EvalSettings
from pipeline.eval import evaluate_offline


def main():
	interactions = pd.read_parquet("data/processed/interactions.parquet")
	settings = EvalSettings.from_env()
	overall, subpop = evaluate_offline(interactions, Path("models"), settings.top_k)

	out_dir = Path("report")
	out_dir.mkdir(parents=True, exist_ok=True)
	overall.to_csv(out_dir / "offline_metrics.csv", index=False)
	subpop.to_csv(out_dir / "offline_subpopulations.csv", index=False)
	print(overall)
	print(subpop)
	print("Saved report/offline_metrics.csv and report/offline_subpopulations.csv")


if __name__ == "__main__":
	main()

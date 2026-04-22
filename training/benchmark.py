# ruff: noqa: E402

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from pipeline.eval import benchmark_models


def main():
	interactions = pd.read_parquet("data/processed/interactions.parquet")
	out_df = benchmark_models(interactions, Path("models"))
	out_dir = Path("report")
	out_dir.mkdir(parents=True, exist_ok=True)
	out_df.to_csv(out_dir / "benchmark.csv", index=False)
	print(out_df)
	print("Saved report/benchmark.csv")


if __name__ == "__main__":
	main()

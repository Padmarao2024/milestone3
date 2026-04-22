# ruff: noqa: E402

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.train import train_als_model


def main():
    interactions = pd.read_parquet("data/processed/interactions.parquet")
    metadata = train_als_model(interactions, Path("models/als"))
    if metadata is None:
        raise RuntimeError(
            "implicit is required for ALS training. Install it in your training env."
        )
    print("Saved ALS model to models/als/model.pkl")


if __name__ == "__main__":
	main()

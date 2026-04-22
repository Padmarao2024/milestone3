# ruff: noqa: E402

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.train import train_popularity_model


def main():
    interactions = pd.read_parquet("data/processed/interactions.parquet")
    train_popularity_model(interactions, Path("models/popularity"))
    print("Saved popularity model to models/popularity/model.pkl")


if __name__ == "__main__":
    main()
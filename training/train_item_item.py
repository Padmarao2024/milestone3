# ruff: noqa: E402

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.train import train_item_item_model


def main():
    interactions = pd.read_parquet("data/processed/interactions.parquet")
    train_item_item_model(interactions, Path("models/item_item"))
    print("Saved item-item model to models/item_item/model.pkl")


if __name__ == "__main__":
    main()
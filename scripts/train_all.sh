#!/bin/bash
export PYTHONPATH="$PWD:${PYTHONPATH}"
python training/prepare_data.py
python training/train_popularity.py
python training/train_item_item.py
python training/train_als.py
python training/evaluate.py
python training/benchmark.py
python training/drift_report.py

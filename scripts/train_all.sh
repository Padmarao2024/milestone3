#!/bin/bash
export PYTHONPATH="$PWD:${PYTHONPATH}"
python3 training/prepare_data.py
python3 training/train_popularity.py
python3 training/train_item_item.py
python3 training/train_als.py
python3 training/evaluate.py
python3 training/benchmark.py
python3 training/drift_report.py

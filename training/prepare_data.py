# ruff: noqa: E402

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.config import Paths
from pipeline.transform import write_processed_frames


def main():
    paths = Paths()
    outputs = write_processed_frames(paths.data_dir)
    for name, output_path in outputs.items():
        print(f"Saved {name} -> {output_path}")


if __name__ == "__main__":
    main()
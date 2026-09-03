"""Reproducible acquisition of the Brazilian E-Commerce Public Dataset by Olist."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import kagglehub

DATASET_HANDLE = "olistbr/brazilian-ecommerce"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DESTINATION = PROJECT_ROOT / "data" / "raw" / "olist"


def download_olist_dataset(destination: Path = DEFAULT_DESTINATION) -> Path:
    """Download the latest Kaggle dataset and copy its original CSVs into RAW."""
    cache_path = Path(kagglehub.dataset_download(DATASET_HANDLE))
    source_files = sorted(cache_path.glob("*.csv"))
    if not source_files:
        raise RuntimeError(f"No CSV files were found in downloaded dataset: {cache_path}")

    destination.mkdir(parents=True, exist_ok=True)
    for source_file in source_files:
        shutil.copy2(source_file, destination / source_file.name)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download the Olist dataset into the RAW layer.")
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    arguments = parser.parse_args()
    raw_path = download_olist_dataset(arguments.destination)
    print(f"Olist dataset copied to: {raw_path}")

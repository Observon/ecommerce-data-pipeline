"""Local entry point for the e-commerce pipeline."""

from __future__ import annotations

import logging
import argparse
from pathlib import Path

from src.ingestion.extract import ExtractionError, extract_csvs

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RAW_DIRECTORY = PROJECT_ROOT / "data" / "raw" / "sample"


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main(raw_directory: Path = SAMPLE_RAW_DIRECTORY) -> None:
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting pipeline")
    try:
        datasets = extract_csvs(raw_directory)
    except ExtractionError:
        logger.exception("Pipeline stopped during extraction")
        raise

    logger.info("Extraction completed for %s datasets", len(datasets))
    logger.info("Pipeline foundation completed successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the e-commerce data pipeline.")
    parser.add_argument(
        "--raw-directory",
        type=Path,
        default=SAMPLE_RAW_DIRECTORY,
        help="Directory containing the six source CSV files.",
    )
    arguments = parser.parse_args()
    main(arguments.raw_directory)

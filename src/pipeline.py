"""Local entry point for the e-commerce pipeline."""

from __future__ import annotations

import logging
import argparse
import json
from pathlib import Path

from src.ingestion.extract import ExtractionError, extract_csvs
from src.quality.checks import validate_datasets
from src.storage.s3 import S3Publisher, S3Settings
from src.transformation.transform import transform_datasets

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RAW_DIRECTORY = PROJECT_ROOT / "data" / "raw" / "sample"
PROCESSED_DIRECTORY = PROJECT_ROOT / "data" / "processed"


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def write_processed_data(processed_directory: Path, valid_datasets: dict, invalid_datasets: dict, report: dict) -> None:
    """Publish valid data and quarantine rejected rows without changing RAW data."""
    quarantine_directory = processed_directory / "quarantine"
    processed_directory.mkdir(parents=True, exist_ok=True)
    quarantine_directory.mkdir(exist_ok=True)
    for dataset, dataframe in valid_datasets.items():
        dataframe.to_parquet(processed_directory / f"{dataset}.parquet", index=False)
    for dataset, dataframe in invalid_datasets.items():
        if not dataframe.empty:
            dataframe.to_parquet(quarantine_directory / f"{dataset}.parquet", index=False)
    (processed_directory / "data_quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def main(
    raw_directory: Path = SAMPLE_RAW_DIRECTORY,
    processed_directory: Path = PROCESSED_DIRECTORY,
    upload_s3: bool = False,
) -> None:
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting pipeline")
    try:
        datasets = extract_csvs(raw_directory)
    except ExtractionError:
        logger.exception("Pipeline stopped during extraction")
        raise

    logger.info("Transforming %s datasets", len(datasets))
    quality_result = validate_datasets(transform_datasets(datasets))
    logger.info("Running data quality checks: %s", quality_result.report["overall_status"])
    write_processed_data(processed_directory, quality_result.valid_datasets, quality_result.invalid_datasets, quality_result.report)
    logger.info("Processed data written to %s", processed_directory)
    if upload_s3:
        publisher = S3Publisher(S3Settings.from_environment())
        raw_keys = publisher.upload_raw_directory(raw_directory)
        processed_keys = publisher.upload_processed_directory(processed_directory)
        logger.info("Uploaded %s RAW and %s PROCESSED artifacts to S3", len(raw_keys), len(processed_keys))
    logger.info("Pipeline completed successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the e-commerce data pipeline.")
    parser.add_argument(
        "--raw-directory",
        type=Path,
        default=SAMPLE_RAW_DIRECTORY,
        help="Directory containing the six source CSV files.",
    )
    parser.add_argument("--processed-directory", type=Path, default=PROCESSED_DIRECTORY, help="Directory for Parquet files and the quality report.")
    parser.add_argument("--upload-s3", action="store_true", help="Publish RAW and PROCESSED artifacts to the configured S3 bucket.")
    arguments = parser.parse_args()
    main(arguments.raw_directory, arguments.processed_directory, arguments.upload_s3)

"""CSV extraction with lightweight structural validation."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

LOGGER = logging.getLogger(__name__)

DATASETS: dict[str, set[str]] = {
    "customers": {"customer_id", "customer_unique_id", "customer_city", "customer_state"},
    "orders": {"order_id", "customer_id", "order_status", "order_purchase_timestamp"},
    "order_items": {"order_id", "order_item_id", "product_id", "price", "freight_value"},
    "products": {"product_id", "product_category_name"},
    "payments": {"order_id", "payment_sequential", "payment_type", "payment_value"},
    "reviews": {"review_id", "order_id", "review_score"},
}


class ExtractionError(RuntimeError):
    """Raised when a raw dataset cannot be safely extracted."""


def extract_csvs(raw_directory: Path) -> dict[str, pd.DataFrame]:
    """Read all required CSVs and enforce the raw data contract."""
    datasets: dict[str, pd.DataFrame] = {}

    for dataset, required_columns in DATASETS.items():
        file_path = raw_directory / f"{dataset}.csv"
        if not file_path.is_file():
            raise ExtractionError(f"Missing required raw file: {file_path}")

        dataframe = pd.read_csv(file_path)
        missing_columns = required_columns.difference(dataframe.columns)
        if missing_columns:
            columns = ", ".join(sorted(missing_columns))
            raise ExtractionError(f"{file_path.name} is missing required columns: {columns}")

        LOGGER.info("Extracted %s: %s rows", dataset, len(dataframe))
        datasets[dataset] = dataframe

    return datasets


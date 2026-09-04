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

OPTIONAL_DATASETS: dict[str, set[str]] = {
    "sellers": {"seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"},
    "geolocation": {
        "geolocation_zip_code_prefix",
        "geolocation_lat",
        "geolocation_lng",
        "geolocation_city",
        "geolocation_state",
    },
    "category_translation": {"product_category_name", "product_category_name_english"},
}

SOURCE_FILENAMES: dict[str, tuple[str, ...]] = {
    "customers": ("customers.csv", "olist_customers_dataset.csv"),
    "orders": ("orders.csv", "olist_orders_dataset.csv"),
    "order_items": ("order_items.csv", "olist_order_items_dataset.csv"),
    "products": ("products.csv", "olist_products_dataset.csv"),
    "payments": ("payments.csv", "olist_order_payments_dataset.csv"),
    "reviews": ("reviews.csv", "olist_order_reviews_dataset.csv"),
    "sellers": ("sellers.csv", "olist_sellers_dataset.csv"),
    "geolocation": ("geolocation.csv", "olist_geolocation_dataset.csv"),
    "category_translation": ("product_category_name_translation.csv",),
}


class ExtractionError(RuntimeError):
    """Raised when a raw dataset cannot be safely extracted."""


def extract_csvs(raw_directory: Path) -> dict[str, pd.DataFrame]:
    """Read all required CSVs and enforce the raw data contract."""
    datasets: dict[str, pd.DataFrame] = {}

    for dataset, required_columns in DATASETS.items():
        file_path = next(
            (raw_directory / filename for filename in SOURCE_FILENAMES[dataset] if (raw_directory / filename).is_file()),
            None,
        )
        if file_path is None:
            expected_files = ", ".join(SOURCE_FILENAMES[dataset])
            raise ExtractionError(f"Missing required raw file for {dataset}. Expected one of: {expected_files}")

        dataframe = pd.read_csv(file_path)
        missing_columns = required_columns.difference(dataframe.columns)
        if missing_columns:
            columns = ", ".join(sorted(missing_columns))
            raise ExtractionError(f"{file_path.name} is missing required columns: {columns}")

        LOGGER.info("Extracted %s: %s rows", dataset, len(dataframe))
        datasets[dataset] = dataframe

    for dataset, required_columns in OPTIONAL_DATASETS.items():
        file_path = next(
            (raw_directory / filename for filename in SOURCE_FILENAMES[dataset] if (raw_directory / filename).is_file()),
            None,
        )
        if file_path is None:
            continue

        dataframe = pd.read_csv(file_path)
        missing_columns = required_columns.difference(dataframe.columns)
        if missing_columns:
            columns = ", ".join(sorted(missing_columns))
            raise ExtractionError(f"{file_path.name} is missing required columns: {columns}")
        LOGGER.info("Extracted optional %s: %s rows", dataset, len(dataframe))
        datasets[dataset] = dataframe

    return datasets

"""Idempotent loading of validated Parquet datasets into PostgreSQL."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import psycopg
from psycopg import sql
from dotenv import load_dotenv


class DatabaseError(RuntimeError):
    """Raised when PostgreSQL configuration or loading fails."""


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    database: str
    user: str
    password: str

    @classmethod
    def from_environment(cls) -> "DatabaseSettings":
        load_dotenv()
        required = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "ecommerce_dw"),
            "user": os.getenv("POSTGRES_USER", "ecommerce"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
        }
        if not required["password"]:
            raise DatabaseError("POSTGRES_PASSWORD must be set for database loading.")
        try:
            port = int(required["port"])
        except ValueError as error:
            raise DatabaseError("POSTGRES_PORT must be an integer.") from error
        return cls(port=port, **{key: value for key, value in required.items() if key != "port"})

    @property
    def connection_string(self) -> str:
        return (
            f"host={self.host} port={self.port} dbname={self.database} "
            f"user={self.user} password={self.password}"
        )


TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "customers": ("customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"),
    "sellers": ("seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"),
    "locations": ("zip_code_prefix", "latitude", "longitude", "city", "state"),
    "products": (
        "product_id", "product_category_name", "product_category_name_english", "product_name_length",
        "product_description_length", "product_photos_qty", "product_weight_g", "product_length_cm",
        "product_height_cm", "product_width_cm",
    ),
    "orders": (
        "order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date",
    ),
    "order_items": (
        "order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value",
    ),
    "payments": ("order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"),
    "reviews": (
        "review_id", "order_id", "review_score", "review_comment_title", "review_comment_message",
        "review_creation_date", "review_answer_timestamp",
    ),
}

PRIMARY_KEYS: dict[str, tuple[str, ...]] = {
    "customers": ("customer_id",),
    "sellers": ("seller_id",),
    "locations": ("zip_code_prefix",),
    "products": ("product_id",),
    "orders": ("order_id",),
    "order_items": ("order_id", "order_item_id"),
    "payments": ("order_id", "payment_sequential"),
    "reviews": ("review_id", "order_id"),
}

LOAD_ORDER = ("customers", "sellers", "locations", "products", "orders", "order_items", "payments", "reviews")


def _prepare_frame(dataset: str, dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataset == "geolocation":
        renamed = dataframe.rename(
            columns={
                "geolocation_zip_code_prefix": "zip_code_prefix",
                "geolocation_lat": "latitude",
                "geolocation_lng": "longitude",
                "geolocation_city": "city",
                "geolocation_state": "state",
            }
        )
        dataset = "locations"
    else:
        renamed = dataframe
    columns = TABLE_COLUMNS[dataset]
    return renamed.reindex(columns=columns)


def _python_value(value: Any) -> Any:
    return None if pd.isna(value) else value


def _upsert_statement(dataset: str) -> sql.Composed:
    columns = TABLE_COLUMNS[dataset]
    keys = PRIMARY_KEYS[dataset]
    updates = tuple(column for column in columns if column not in keys)
    return sql.SQL("INSERT INTO {table} ({columns}) VALUES ({values}) ON CONFLICT ({keys}) DO UPDATE SET {updates}").format(
        table=sql.Identifier(dataset),
        columns=sql.SQL(", ").join(map(sql.Identifier, columns)),
        values=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        keys=sql.SQL(", ").join(map(sql.Identifier, keys)),
        updates=sql.SQL(", ").join(
            sql.SQL("{column} = EXCLUDED.{column}").format(column=sql.Identifier(column)) for column in updates
        ),
    )


def load_datasets(connection: Any, datasets: dict[str, pd.DataFrame]) -> dict[str, int]:
    """Upsert validated datasets in FK order inside the caller's transaction."""
    loaded: dict[str, int] = {}
    with connection.cursor() as cursor:
        for dataset in LOAD_ORDER:
            source_name = "geolocation" if dataset == "locations" else dataset
            dataframe = datasets.get(source_name)
            if dataframe is None or dataframe.empty:
                continue
            prepared = _prepare_frame(source_name, dataframe)
            records = [tuple(_python_value(value) for value in row) for row in prepared.itertuples(index=False, name=None)]
            cursor.executemany(_upsert_statement(dataset), records)
            loaded[dataset] = len(records)
    return loaded


def load_processed_directory(
    processed_directory: Path,
    settings: DatabaseSettings,
    connection_factory: Callable[..., Any] = psycopg.connect,
) -> dict[str, int]:
    """Load processed Parquets using one committed transaction."""
    datasets = {
        path.stem: pd.read_parquet(path)
        for path in processed_directory.glob("*.parquet")
        if path.stem in TABLE_COLUMNS or path.stem == "geolocation"
    }
    with connection_factory(settings.connection_string) as connection:
        loaded = load_datasets(connection, datasets)
        connection.commit()
    return loaded
import os
from pathlib import Path
from typing import Any

import psycopg
import pytest

from src.database.loader import DatabaseSettings, load_processed_directory

pytestmark = pytest.mark.integration


def _integration_enabled() -> bool:
    return os.getenv("POSTGRES_INTEGRATION", "").lower() in {"1", "true", "yes"}


def _scalar(cursor: Any) -> Any:
    row = cursor.fetchone()
    if row is None:
        raise AssertionError("Expected PostgreSQL query to return one row.")
    return row[0]


@pytest.mark.skipif(not _integration_enabled(), reason="Set POSTGRES_INTEGRATION=1 to run PostgreSQL integration tests.")
def test_processed_load_is_idempotent_and_reconciles_revenue() -> None:
    settings = DatabaseSettings.from_environment()
    processed_directory = Path("data/processed")

    load_processed_directory(processed_directory, settings)
    load_processed_directory(processed_directory, settings)

    with psycopg.connect(settings.connection_string) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM order_items")
            operational_items = _scalar(cursor)
            cursor.execute("SELECT COUNT(*) FROM fact_order_item")
            analytical_items = _scalar(cursor)
            cursor.execute("SELECT ROUND(SUM(price + freight_value), 2) FROM order_items")
            operational_revenue = _scalar(cursor)
            cursor.execute("SELECT ROUND(SUM(price + freight_value), 2) FROM fact_order_item")
            analytical_revenue = _scalar(cursor)

    assert operational_items == analytical_items
    assert operational_revenue == analytical_revenue
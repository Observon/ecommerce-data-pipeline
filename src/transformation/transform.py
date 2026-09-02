"""Cleaning, typing and business-derived attributes for raw e-commerce data."""

from __future__ import annotations

import pandas as pd

DATETIME_COLUMNS: dict[str, list[str]] = {
    "orders": [
        "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
        "order_delivered_customer_date", "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}


def _clean_text(series: pd.Series, *, uppercase: bool = False) -> pd.Series:
    cleaned = series.astype("string").str.strip()
    return cleaned.str.upper() if uppercase else cleaned


def _parse_datetimes(dataframe: pd.DataFrame, dataset: str) -> pd.DataFrame:
    transformed = dataframe.copy()
    for column in DATETIME_COLUMNS.get(dataset, []):
        transformed[column] = pd.to_datetime(transformed[column], errors="coerce")
    return transformed


def transform_datasets(datasets: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Standardize raw data and add attributes without mutating the input frames."""
    transformed = {name: _parse_datetimes(frame, name) for name, frame in datasets.items()}

    customers = transformed["customers"]
    for column in ("customer_id", "customer_unique_id", "customer_city"):
        customers[column] = _clean_text(customers[column])
    customers["customer_state"] = _clean_text(customers["customer_state"], uppercase=True)
    customers["customer_zip_code_prefix"] = pd.to_numeric(customers["customer_zip_code_prefix"], errors="coerce").astype("Int64")

    products = transformed["products"]
    products["product_id"] = _clean_text(products["product_id"])
    products["product_category_name"] = _clean_text(products["product_category_name"])
    for column in products.columns.difference(["product_id", "product_category_name"]):
        products[column] = pd.to_numeric(products[column], errors="coerce")

    orders = transformed["orders"]
    orders["order_id"] = _clean_text(orders["order_id"])
    orders["customer_id"] = _clean_text(orders["customer_id"])
    orders["order_status"] = _clean_text(orders["order_status"]).str.lower()

    order_items = transformed["order_items"]
    for column in ("order_id", "product_id"):
        order_items[column] = _clean_text(order_items[column])
    order_items["order_item_id"] = pd.to_numeric(order_items["order_item_id"], errors="coerce").astype("Int64")
    for column in ("price", "freight_value"):
        order_items[column] = pd.to_numeric(order_items[column], errors="coerce")

    payments = transformed["payments"]
    payments["order_id"] = _clean_text(payments["order_id"])
    payments["payment_type"] = _clean_text(payments["payment_type"]).str.lower()
    payments["payment_sequential"] = pd.to_numeric(payments["payment_sequential"], errors="coerce").astype("Int64")
    payments["payment_installments"] = pd.to_numeric(payments["payment_installments"], errors="coerce").astype("Int64")
    payments["payment_value"] = pd.to_numeric(payments["payment_value"], errors="coerce")

    reviews = transformed["reviews"]
    reviews["review_id"] = _clean_text(reviews["review_id"])
    reviews["order_id"] = _clean_text(reviews["order_id"])
    reviews["review_score"] = pd.to_numeric(reviews["review_score"], errors="coerce").astype("Int64")

    totals = order_items.assign(line_total=order_items["price"] + order_items["freight_value"])
    order_totals = totals.groupby("order_id", dropna=False)["line_total"].sum().rename("order_total")
    orders["order_total"] = orders["order_id"].map(order_totals).fillna(0.0)
    orders["delivery_days"] = (orders["order_delivered_customer_date"] - orders["order_purchase_timestamp"]).dt.total_seconds() / 86_400
    return transformed

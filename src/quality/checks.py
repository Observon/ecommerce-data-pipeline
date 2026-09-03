"""Row-level data quality checks and audit report generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class QualityResult:
    valid_datasets: dict[str, pd.DataFrame]
    invalid_datasets: dict[str, pd.DataFrame]
    report: dict[str, Any]


def _empty_mask(dataframe: pd.DataFrame) -> pd.Series:
    return pd.Series(False, index=dataframe.index)


def _missing_key(dataframe: pd.DataFrame, columns: list[str]) -> pd.Series:
    return dataframe[columns].isna().any(axis=1) | dataframe[columns].eq("").any(axis=1)


def _report_entry(dataframe: pd.DataFrame, invalid_mask: pd.Series, metrics: dict[str, int]) -> dict[str, int | str]:
    rows_received = len(dataframe)
    invalid_rows = int(invalid_mask.sum())
    status = "FAIL" if rows_received == 0 else "WARNING" if invalid_rows else "PASS"
    return {"rows_received": rows_received, "valid_rows": rows_received - invalid_rows, "invalid_rows": invalid_rows, **metrics, "status": status}


def validate_datasets(datasets: dict[str, pd.DataFrame]) -> QualityResult:
    """Validate business keys, references, numeric bounds and required dates."""
    invalid_masks = {name: _empty_mask(frame) for name, frame in datasets.items()}
    metrics: dict[str, dict[str, int]] = {name: {} for name in datasets}

    def add_rule(dataset: str, name: str, failing_rows: pd.Series) -> None:
        invalid_masks[dataset] |= failing_rows
        metrics[dataset][name] = int(failing_rows.sum())

    customers = datasets["customers"]
    add_rule("customers", "missing_ids", _missing_key(customers, ["customer_id"]))
    add_rule("customers", "duplicates", customers.duplicated(["customer_id"], keep=False))
    valid_customer_ids = set(customers.loc[~invalid_masks["customers"], "customer_id"])

    products = datasets["products"]
    add_rule("products", "missing_ids", _missing_key(products, ["product_id"]))
    add_rule("products", "duplicates", products.duplicated(["product_id"], keep=False))
    valid_product_ids = set(products.loc[~invalid_masks["products"], "product_id"])

    orders = datasets["orders"]
    add_rule("orders", "missing_ids", _missing_key(orders, ["order_id"]))
    add_rule("orders", "duplicates", orders.duplicated(["order_id"], keep=False))
    add_rule("orders", "invalid_dates", orders["order_purchase_timestamp"].isna())
    add_rule("orders", "referential_integrity_violations", ~orders["customer_id"].isin(valid_customer_ids) | _missing_key(orders, ["customer_id"]))
    valid_order_ids = set(orders.loc[~invalid_masks["orders"], "order_id"])

    order_items = datasets["order_items"]
    item_key = ["order_id", "order_item_id"]
    add_rule("order_items", "missing_ids", _missing_key(order_items, item_key + ["product_id"]))
    add_rule("order_items", "duplicates", order_items.duplicated(item_key, keep=False))
    add_rule("order_items", "negative_amounts", order_items[["price", "freight_value"]].lt(0).any(axis=1) | order_items[["price", "freight_value"]].isna().any(axis=1))
    add_rule("order_items", "referential_integrity_violations", ~order_items["order_id"].isin(valid_order_ids) | ~order_items["product_id"].isin(valid_product_ids))

    payments = datasets["payments"]
    payment_key = ["order_id", "payment_sequential"]
    add_rule("payments", "missing_ids", _missing_key(payments, payment_key))
    add_rule("payments", "duplicates", payments.duplicated(payment_key, keep=False))
    add_rule("payments", "negative_amounts", payments["payment_value"].isna() | payments["payment_value"].lt(0))
    add_rule("payments", "referential_integrity_violations", ~payments["order_id"].isin(valid_order_ids))

    reviews = datasets["reviews"]
    add_rule("reviews", "missing_ids", _missing_key(reviews, ["review_id", "order_id"]))
    add_rule("reviews", "duplicates", reviews.duplicated(["review_id", "order_id"], keep=False))
    add_rule("reviews", "invalid_review_scores", reviews["review_score"].isna() | ~reviews["review_score"].between(1, 5))
    add_rule("reviews", "referential_integrity_violations", ~reviews["order_id"].isin(valid_order_ids))

    valid_datasets = {name: frame.loc[~invalid_masks[name]].copy() for name, frame in datasets.items()}
    invalid_datasets = {name: frame.loc[invalid_masks[name]].copy() for name, frame in datasets.items()}
    report = {
        "overall_status": "WARNING" if any(mask.any() for mask in invalid_masks.values()) else "PASS",
        "datasets": {name: _report_entry(frame, invalid_masks[name], metrics[name]) for name, frame in datasets.items()},
    }
    return QualityResult(valid_datasets, invalid_datasets, report)

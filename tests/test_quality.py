from pathlib import Path

import pandas as pd

from src.ingestion.extract import extract_csvs
from src.quality.checks import validate_datasets
from src.transformation.transform import transform_datasets


def test_quality_rejects_negative_prices() -> None:
    datasets = transform_datasets(extract_csvs(Path("data/raw/sample")))
    datasets["order_items"].loc[0, "price"] = -1

    result = validate_datasets(datasets)

    assert result.report["overall_status"] == "WARNING"
    assert result.report["datasets"]["order_items"]["invalid_rows"] == 1
    assert len(result.valid_datasets["order_items"]) == 2
    assert len(result.invalid_datasets["order_items"]) == 1


def test_quality_rejects_children_of_an_invalid_parent() -> None:
    datasets = transform_datasets(extract_csvs(Path("data/raw/sample")))
    datasets["customers"].loc[1, "customer_id"] = "cus_001"

    result = validate_datasets(datasets)

    assert result.report["datasets"]["customers"]["invalid_rows"] == 2
    assert result.report["datasets"]["orders"]["invalid_rows"] == 2


def test_quality_allows_a_review_id_on_different_orders() -> None:
    datasets = transform_datasets(extract_csvs(Path("data/raw/sample")))
    duplicated_review = datasets["reviews"].iloc[[0]].copy()
    duplicated_review.loc[:, "order_id"] = "ord_002"
    datasets["reviews"] = pd.concat([datasets["reviews"], duplicated_review], ignore_index=True)

    result = validate_datasets(datasets)

    assert result.report["datasets"]["reviews"]["invalid_rows"] == 0

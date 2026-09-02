from pathlib import Path

from src.ingestion.extract import extract_csvs
from src.transformation.transform import transform_datasets


def test_orders_include_total_and_delivery_duration() -> None:
    orders = transform_datasets(extract_csvs(Path("data/raw/sample")))["orders"].set_index("order_id")

    assert orders.loc["ord_001", "order_total"] == 224.8
    assert orders.loc["ord_001", "delivery_days"] == 4.145833333333333
    assert orders.loc["ord_003", "order_total"] == 0.0

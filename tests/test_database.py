from typing import Any

import pandas as pd

from src.database.loader import load_datasets


class FakeCursor:
    def __init__(self, calls: list[tuple[str, list[tuple[Any, ...]]]]) -> None:
        self.calls = calls

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def executemany(self, statement: Any, records: list[tuple[Any, ...]]) -> None:
        self.calls.append((str(statement), records))


class FakeConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[tuple[Any, ...]]]] = []
        self.commits = 0

    def cursor(self) -> FakeCursor:
        return FakeCursor(self.calls)

    def commit(self) -> None:
        self.commits += 1


def test_load_datasets_uses_fk_order_and_upsert() -> None:
    connection = FakeConnection()
    datasets = {
        "customers": pd.DataFrame(
            [{"customer_id": "cus_001", "customer_unique_id": "unique_001", "customer_city": "Campinas", "customer_state": "SP"}]
        ),
        "orders": pd.DataFrame(
            [{"order_id": "ord_001", "customer_id": "cus_001", "order_status": "delivered", "order_purchase_timestamp": pd.Timestamp("2024-01-01")}]
        ),
    }

    loaded = load_datasets(connection, datasets)

    assert loaded == {"customers": 1, "orders": 1}
    assert "customers" in repr(connection.calls[0][0])
    assert "orders" in repr(connection.calls[1][0])
    assert all("ON CONFLICT" in call[0] for call in connection.calls)
    assert connection.calls[1][1][0][0:2] == ("ord_001", "cus_001")
from pathlib import Path

from src.storage.s3 import S3Publisher, S3Settings


class FakeS3Client:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, str, str]] = []

    def upload_file(self, filename: str, bucket: str, key: str) -> None:
        self.uploads.append((filename, bucket, key))


def test_publisher_preserves_raw_filenames_and_layer(tmp_path: Path) -> None:
    raw_directory = tmp_path / "olist"
    raw_directory.mkdir()
    (raw_directory / "olist_orders_dataset.csv").write_text("order_id\n1\n", encoding="utf-8")
    client = FakeS3Client()
    publisher = S3Publisher(S3Settings(bucket="test-bucket", region="us-east-1"), client=client)

    keys = publisher.upload_raw_directory(raw_directory)

    assert keys == ["raw/olist/olist_orders_dataset.csv"]
    assert client.uploads[0][1:] == ("test-bucket", "raw/olist/olist_orders_dataset.csv")


def test_publisher_uploads_processed_report_and_quarantine(tmp_path: Path) -> None:
    processed_directory = tmp_path / "processed"
    quarantine_directory = processed_directory / "quarantine"
    quarantine_directory.mkdir(parents=True)
    (processed_directory / "orders.parquet").write_bytes(b"parquet")
    (processed_directory / "data_quality_report.json").write_text("{}", encoding="utf-8")
    (quarantine_directory / "reviews.parquet").write_bytes(b"parquet")
    client = FakeS3Client()
    publisher = S3Publisher(S3Settings(bucket="test-bucket", region="us-east-1"), client=client)

    keys = publisher.upload_processed_directory(processed_directory)

    assert keys == [
        "processed/data_quality_report.json",
        "processed/orders.parquet",
        "processed/quarantine/reviews.parquet",
    ]

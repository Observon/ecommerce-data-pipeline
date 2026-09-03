from pathlib import Path

from src.ingestion.extract import DATASETS, SOURCE_FILENAMES, extract_csvs


def test_sample_files_follow_extraction_contract() -> None:
    raw_directory = Path("data/raw/sample")

    datasets = extract_csvs(raw_directory)

    assert set(datasets) == set(DATASETS)
    assert all(not dataframe.empty for dataframe in datasets.values())


def test_official_olist_filenames_are_supported() -> None:
    assert SOURCE_FILENAMES["orders"] == ("orders.csv", "olist_orders_dataset.csv")
    assert SOURCE_FILENAMES["payments"] == ("payments.csv", "olist_order_payments_dataset.csv")

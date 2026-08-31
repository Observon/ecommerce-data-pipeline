from pathlib import Path

from src.ingestion.extract import DATASETS, extract_csvs


def test_sample_files_follow_extraction_contract() -> None:
    raw_directory = Path("data/raw/sample")

    datasets = extract_csvs(raw_directory)

    assert set(datasets) == set(DATASETS)
    assert all(not dataframe.empty for dataframe in datasets.values())

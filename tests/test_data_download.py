import os
from pathlib import Path

import pytest

from utils import download_file, download_test_data


@pytest.fixture
def zip_file_path():
    return Path("./testdata/HNSCC.zip")


@pytest.fixture
def data_path():
    return Path("./testdata")


# ID001: Test for downloading a file.
def test_download_file_successful(data_path):
    data_path.mkdir(parents=True, exist_ok=True)

    zip_path = data_path / "HNSCC.zip"
    download_file(
        "https://zenodo.org/record/5276878/files/HNSCC.zip",
        "6332d59406978a92f57d15da84f2e143",
        zip_path,
    )

    assert zip_path.exists()


# ID002: Test for hash mismatch
def test_download_file_unsuccessful(data_path):
    with pytest.raises(ValueError) as exc_info:
        download_file(
            "https://zenodo.org/record/5276878/files/HNSCC.zip",
            "6332d59406978a88f57d15da84f2e143",
            data_path.joinpath("HNSCC.zip"),
        )
    assert "Hash mismatch" in str(exc_info.value)


# ID003: Download test data - full process
def test_download_test_data(zip_file_path, data_path):
    download_test_data(data_path)

    # Assert ZIP file was deleted
    assert not zip_file_path.exists()

    # Assert expected directories exist
    extracted_path = data_path / "HNSCC"

    for name in ["HNSCC-01-0019", "HNSCC-01-0176", "HNSCC-01-0199"]:
        assert extracted_path.joinpath(name).is_dir()

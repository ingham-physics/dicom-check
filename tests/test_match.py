import json
from pathlib import Path

import pytest

from match import match_series_to_template


@pytest.fixture
def dicom_path():
    return Path("testdata/HNSCC/HNSCC-01-0176")


@pytest.fixture
def series_file(dicom_path):
    return dicom_path / "series.json"


@pytest.fixture
def template_dict():
    return Path("templates/generic-rt.json")


EXPECTED_MATCHES = 8


# ID014
def test_match_series_to_template(dicom_path, series_file, template_dict):

    match_series_to_template(
        directory=dicom_path, template=template_dict, report_format="pdf"
    )

    # Count the number of matches
    with open(series_file, "r", encoding="utf-8") as f:
        series_json = json.load(f)

    matches = [elem for elem in series_json["series"] if "match" in elem.keys()]

    assert len(matches) == EXPECTED_MATCHES

import json
from pathlib import Path

import pytest

from check import perform_checks, find_matched_series


@pytest.fixture
def dicom_path():
    return Path("testdata/HNSCC/HNSCC-01-0176")


@pytest.fixture
def series_file(dicom_path):
    return dicom_path / "series.json"


@pytest.fixture
def template_dict():
    return Path("templates/generic-rt.json")


NUM_PASS = 7
NUM_FAIL = 6

# For each scenario there are a number of expected outputs
cases_per_series = [
    {"name": "Planning CT", "expected_matches": 2},
    {"name": "RT Structure Set", "expected_matches": 2},
    {"name": "RT Plan", "expected_matches": 2},
    {"name": "RT Dose", "expected_matches": 2},
    {"name": ["Planning CT", "RT Structure Set"], "expected_matches": 4},
    {"name": ["RT Structure Set", "RT Plan"], "expected_matches": 4},
    {"name": ["RT Plan", "RT Dose"], "expected_matches": 4},
    {
        "name": ["Planning CT", "RT Structure Set", "RT Plan", "RT Dose"],
        "expected_matches": 8,
    },
]


# ID015
@pytest.mark.parametrize(
    "case", cases_per_series, ids=[str(c["name"]) for c in cases_per_series]
)
def test_find_matched_series(case, series_file):

    with open(series_file, "r", encoding="utf-8") as f:
        series_json = json.load(f)

    result = find_matched_series(series_json=series_json, name=case["name"])
    assert len(result) == case["expected_matches"], f"Failed for: {case['name']}"


# ID016
def test_perform_checks(dicom_path, series_file, template_dict):

    perform_checks(directory=dicom_path, template=template_dict, report_format="pdf")

    with open(series_file, "r", encoding="utf-8") as f:
        series_json = json.load(f)

    all_checks = series_json["checks"]
    passed = [check for check in all_checks if check["passed"]]
    failed = [check for check in all_checks if not check["passed"]]

    assert len(passed) == NUM_PASS
    assert len(failed) == NUM_FAIL

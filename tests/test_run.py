from pathlib import Path

import pandas as pd
import pytest

from run import run_on_all_subdirectories


@pytest.fixture
def dicom_path():
    return Path("testdata/HNSCC")


@pytest.fixture
def template_dict():
    return "templates/generic-rt.json"


def test_run_on_all_subdirectories(
    dicom_path,
    template_dict,
):

    # Run the processing on all subdirectories
    run_on_all_subdirectories(
        directory=dicom_path, template=template_dict, report_format="pdf"
    )

    result_df = pd.read_csv("testdata/HNSCC/check_results.csv")
    result_df = result_df.sort_values("directory").reset_index(drop=True)

    # Check results
    assert len(result_df["directory"].unique()) == 3
    assert result_df["Check if Planning CT is present"].tolist() == [True, True, True]
    assert result_df["Check we have exactly one Planning CT"].tolist() == [
        True,
        False,
        True,
    ]
    assert result_df["Check if RT Structure Set is present"].tolist() == [
        True,
        True,
        True,
    ]
    assert result_df["Check we have exactly one RT Structure Set"].tolist() == [
        True,
        False,
        True,
    ]
    assert result_df["Check expected structures present in structure set"].tolist() == [
        False,
        False,
        False,
    ]
    assert result_df["Check if RT Plan is present"].tolist() == [True, True, True]
    assert result_df["Check if RT Dose is present"].tolist() == [True, True, True]

    assert result_df["Check if RT Dose DoseSummationType is PLAN"].tolist() == [
        True,
        True,
        True,
    ]
    assert result_df["Check all series in same Frame of Reference"].tolist() == [
        True,
        False,
        True,
    ]
    assert result_df["Check all series in same Study"].tolist() == [True, False, True]
    assert result_df["Check RTSTRUCT and Planning CT are linked"].tolist() == [
        True,
        True,
        True,
    ]
    assert result_df["Check RTPLAN and RTSTRUCT are linked"].tolist() == [
        True,
        False,
        True,
    ]
    assert result_df["Check RTDOSE and RTPLAN are linked"].tolist() == [
        True,
        True,
        True,
    ]

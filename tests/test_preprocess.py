from pathlib import Path

import pandas as pd
import pytest

from preprocess import (
    generate_series_json,
    generate_series_report,
    index_dicom_files,
    load_template,
    preprocess,
    scan_file,
)

from utils import download_font_pack


@pytest.fixture
def expected_template_keys():
    return ["project", "description", "version", "meta", "expected_series", "checks"]


@pytest.fixture
def dicom_path():
    return Path("testdata/HNSCC/HNSCC-01-0176")


@pytest.fixture
def dicom_file(dicom_path):
    return dicom_path / "03-01-2009-NA-NA-44207" / "10.000000-NA-34598" / "135-001.dcm"


@pytest.fixture
def template_file():
    return Path("templates/generic-rt.json")


expected_df_cols = [
    "patient_id",
    "study_uid",
    "series_uid",
    "modality",
    "sop_class_uid",
    "sop_instance_uid",
    "for_uid",
    "file_path",
    "date_time",
    "slice_location",
    "referenced_uid",
    "referenced_for_uid",
    "SeriesDescription",
    "StudyDescription",
    "StudyInstanceUID",
    "DoseSummationType",
]


# ID004
def test_load_template(template_file, expected_template_keys):

    template_dict = load_template(template_file)
    assert expected_template_keys == list(template_dict.keys())


# ID005
def test_index_dicom_file_value_error():

    # Provide incorrect argument type
    with pytest.raises(ValueError) as exc_info:
        index_dicom_files(1)

    assert "input_directory must be of type pathlib.Path or str" in str(exc_info.value)


# ID006
def test_index_dicom_file_successful(template_file, dicom_path):

    # Load the files from example DICOM dir.
    template = load_template(template_file)
    meta = template.get("meta", [])
    dicom_df = index_dicom_files(dicom_path, meta=meta)

    assert dicom_df.shape == (998, 16)
    assert list(dicom_df.columns) == expected_df_cols


# # ID007 - Not in the README
# def test_scan_file_unsuccessful(template_file):

#     # Provide a non-DICOM file
#     template = load_template(template_file)
#     meta = template.get("meta", [])
#     result, status, _ = scan_file(template, meta=meta)

#     assert result is None
#     assert status == "error"

#     # Provide a random DICOM file
#     f = r"testdata/HNSCC/HNSCC-01-0019/07-04-1998-NA-RT\ SIMULATION-48452/1.000000-NA-10361/1-1.dcm"
#     result, status, _ = scan_file(f, meta=meta)

#     assert result is None
#     assert status == "error"


# # ID008 - Not in the README
# def test_scan_file_successful(template_file, dicom_file):

#     # Load in the meta tags
#     template = load_template(template_file)
#     meta = template.get("meta", [])

#     # Provide a DICOM file that can be indexed
#     result, status, _ = scan_file(dicom_file, meta=meta)

#     assert result is not None
#     assert status == "ok"
#     assert isinstance(result, dict)
#     assert result["patient_id"] == "HNSCC-01-0176"


# ID009
def test_generate_series_json_unsuccessful(template_file, dicom_file):

    # Load in the meta tags
    template = load_template(template_file)
    meta = template.get("meta", [])

    # Provide a DICOM file that can be indexed
    dicom_dict1, _, _ = scan_file(dicom_file, meta=meta)
    dicom_dict2, _, _ = scan_file(dicom_file, meta=meta)

    assert dicom_dict1 is not None
    assert dicom_dict2 is not None

    dicom_dict2_copy = dicom_dict2

    # Go through the 'cases' that will raise a ValueError
    cases = {
        "modality": " has multiple modalities",
        "for_uid": " has multiple frame of references",
        "referenced_uid": " has multiple referenced series",
    }

    for case, message in cases.items():

        dicom_dict2_copy[case] = "something_random"

        dicom_df = pd.DataFrame(
            [dicom_dict1, dicom_dict2_copy], columns=expected_df_cols
        )

        with pytest.raises(ValueError) as exc_info:
            generate_series_json(df=dicom_df, meta=meta)

        assert f"Series {list(dicom_df['series_id'])[0]}" + message in str(
            exc_info.value
        )


# ID010
def test_generate_series_json_successful(template_file, dicom_file):

    # Load in the meta tags
    template = load_template(template_file)
    meta = template.get("meta", [])

    # Provide a DICOM file that can be indexed
    dicom_dict1, _, _ = scan_file(dicom_file, meta=meta)
    dicom_dict2, _, _ = scan_file(dicom_file, meta=meta)

    assert dicom_dict1 is not None
    assert dicom_dict2 is not None

    dicom_df = pd.DataFrame([dicom_dict1, dicom_dict2], columns=expected_df_cols)
    series_json = generate_series_json(df=dicom_df, meta=meta)

    assert isinstance(series_json, dict)


# ID011
def test_generate_series_report_unsuccessful():

    # Provide invalid report format
    incorrect_report_format = "py"
    with pytest.raises(ValueError) as exc_info:
        generate_series_report(
            series_json={}, output_directory=".", report_format=incorrect_report_format
        )

        assert f"Unsupported format {incorrect_report_format}" in str(exc_info.value)


# ID012
def test_download_font_pack_successful():

    download_font_pack(Path("."))

    zip_file_path = Path("./font_pack.zip")

    # Assert ZIP file was deleted
    assert not zip_file_path.exists()


# ID013
def test_preprocess(dicom_path, template_file):

    # Run the whole preprocess task
    preprocess(input_directory=dicom_path, template=template_file, report_format="pdf")

    # Check that the indexed.csv is created
    indexed_file = dicom_path.joinpath("indexed.csv")
    assert indexed_file.exists()

    # Check that the series.json is created
    series_file = dicom_path.joinpath("series.json")
    assert series_file.exists()

    # Check that the pdf report is present
    series_report = dicom_path.joinpath("series_report.pdf")
    assert series_report.exists()

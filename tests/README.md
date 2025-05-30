# `dicom-check tests`

This folder contains unit and integration tests that are run as part of GitHub Actions, but can also be run locally in the following order, corresponding to the sequential pipeline steps:
```
# Step 1: Download test data
python -m pytest tests/test_data_download.py

# Step 2: Preprocess DICOM files
python -m pytest tests/test_preprocess.py

# Step 3: Match series to template
python -m pytest tests/test_match.py

# Step 4: Perform a series of checks
python -m pytest tests/test_check.py

# Step 5: Run the full workflow on all subdirectories
python -m pytest tests/test_run.py
```

## Test summary table
Each table below summarises the test scripts, their assigned IDs, purpose, and the key functions they utilise.


### `test_data_download.py`

| Test-ID | Test name | Description | Functions tested |
| -------- | ------- | -------- | ------- |
| ID001 | `test_download_file_successful` | Tests successful file download | download_file |
| ID002 | `test_download_file_unsuccessful` | Tests hash mismatch handling during download | download_file |
| ID003 | `test_download_test_data` | Tests full test data download and extraction process | download_test_data |


### `test_preprocess.py`

| Test-ID | Test name | Description | Functions tested |
| -------- | ------- | -------- | ------- |
| ID004 | `test_load_template` | Validates loading of the template file and its structure | load_template |
| ID005| `test_index_dicom_file_value_error` | Tests error handling for incorrect input type | index_dicom_files |
| ID006 | `test_index_dicom_file_successful` | Tests correct indexing of DICOM files and DataFrame structure | load_template, index_dicom_files |
| ID009 | `test_generate_series_json_unsuccessful` | Validates detection of data inconsistencies during JSON generation | load_template, scan_file |
| ID010 | `test_generate_series_json_successful` | Tests successful creation of series JSON from scanned DICOM data | load_template, scan_file |
| ID011 | `test_generate_series_report_unsuccessful` | Tests error raised for unsupported report format | generate_series_report |
| ID012 | `test_download_font_pack_successful` | Checks whether font pack downloads and unzips correctly | download_font_pack |
| ID013 | `test_preprocess` | Tests the whole preprocessing step including file generation | download_font_pack |

**Note:** IDs ID007 and ID008 are not included in the table, until Phil advises me on the scan_file question I have.

### `test_match.py`

| Test-ID | Test name | Description | Functions tested |
| -------- | ------- | -------- | -------  |
| ID014 | `test_match_series_to_template` | Validates series matching based on template, and checks match count | match_series_to_template |


### `test_check.py`

| Test-ID | Test name |  Description | Functions tested |
| -------- | ------- | -------- | -------- |
| ID015 | `test_find_matched_series` | Validates matching logic for different checks and expected match counts | find_matched_series |
| ID016 | `test_perform_checks` | Compares number of passed/failed checks with expected outcome | perform_checks |


### `test_run.py`

| Test-ID | Test name | Description | Functions tested |
| -------- | ------- |  ------- | -------- |
| ID017 | test_run_on_all_subdirectories | Executes full pipeline on all subdirectories and validates the final summary table | run_on_all_subdirectories |

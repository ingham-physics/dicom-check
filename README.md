# DICOM Check

A tool to index DICOM data and perform some checks for data completeness.

> This tool is under development and is intended for experimentation use only.

## Usage

### Install Requirements

You can pip install the requirements.txt file to install all dependencies:

```bash
pip install -r requirements.txt
```

### Test data

Pull some test data for experimentation (HNSCC from The Cancer Imaging Archive):

```bash
python test.py
```

### Preprocess

Indexes DICOM data in a directory and produces a report with DICOM series found.

```bash
python preprocess.py -t templates/generic-rt.json -r pdftestdata/HNSCC/HNSCC-01-0176
```

For all options use the command line interface help:

```bash
python preprocess.py --help
```

### Match

Maches DICOM series to a template provided.

```bash
python match.py -t templates/generic-rt.json -r pdf testdata/HNSCC/HNSCC-01-0176
```

For all options use the command line interface help:

```bash
python match.py --help
```

### Check

Peforms checks defined in template against series data.

```bash
python check.py -t templates/generic-rt.json -r pdftestdata/HNSCC/HNSCC-01-0176
```

For all options use the command line interface help:

```bash
python check.py --help
```

### Run on all sub-directories

Run all steps on each sub-directory of a directory:

```bash
python run.py -t templates/generic-rt.json -r pdftestdata/HNSCC
```

Check the `testdata/HNSCC/check_results.csv` for a summary of all checks performed.

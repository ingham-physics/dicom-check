# DICOM Check

A tool to index DICOM data and perform some checks for data completeness.

## Usage

### Test data

Pull some test data for experimentation (HNSCC from The Cancer Imaging Archive):

```bash
python test.py
```

### Preprocess

Indexes DICOM data in a directory and produces a report with DICOM series found.

```bash
python preprocess.py testdata/HNSCC/HNSCC-01-0176 -t templates/generic-rt.json -r pdf
```

For all options use the command line interface help:

```bash
python preprocess.py --help
```

### Match

Maches DICOM series to a template provided.

```bash
python match.py testdata/HNSCC/HNSCC-01-0176 -t templates/generic-rt.json -r pdf
```

For all options use the command line interface help:

```bash
python match.py --help
```

### Check

Peforms checks defined in template against series data.

```bash
python check.py testdata/HNSCC/HNSCC-01-0176 -t templates/generic-rt.json -r pdf
```

For all options use the command line interface help:

```bash
python match.py --help
```

### Run on all sub-directories

Run all steps on each sub-directory of a directory:

```bash
python run.py testdata/HNSCC -t templates/generic-rt.json -r pdf
```

Check the `testdata/HNSCC/check_results.csv` for a summary of all checks performed.

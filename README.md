# DICOM Check

A tool to index DICOM data and perform some checks for data completeness.

## Usage

### Preprocess

Indexes DICOM data in a directory and produces a report with DICOM series found.

```bash
python preprocess.py -m StudyDescription SeriesDescription [input_directory]
```

For all options use the command line interface help:

```bash
python preprocess.py --help
```

### Match

Maches DICOM series to a template provided.

```bash
python match.py -t templates/generic-rt.json [input_directory]
```

For all options use the command line interface help:

```bash
python match.py --help
```

### Check

Run checks defined in template on the DICOM series matched.

> Coming soon

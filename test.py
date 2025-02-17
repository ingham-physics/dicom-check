import argparse
from pathlib import Path

from utils import download_test_data

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Download test data.")
    parser.add_argument(
        "-d", "--directory",
        type=Path,
        help="The path in which DICOM series were preprocessed.",
    )

    args = parser.parse_args()

    directory = Path("./testdata")
    if args.directory is not None:
        directory = args.directory

    download_test_data(directory)

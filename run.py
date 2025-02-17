import json
from pathlib import Path
from typing import Optional

import pandas as pd

from preprocess import preprocess
from match import match_series_to_template
from check import perform_checks

def run_on_all_subdirectories(directory: Path, template: str, report_format: Optional[str] = None):
    """Run a script on all sub-directories in a directory.

    Args:
        directory (Path): The directory to process.
        template (str): The path to the template JSON file.
        report_format (str): The format of the report to generate (pdf or html). If not
            provided, no report is generated.
    """

    check_results = []

    for subdirectory in directory.iterdir():
        if subdirectory.is_dir():
            preprocess(
                input_directory=subdirectory,
                template=template,
                report_format=report_format,
                output_directory=subdirectory,
            )

            match_series_to_template(
                directory=subdirectory,
                template=template,
                report_format=report_format,
            )

            perform_checks(
                directory=subdirectory,
                template=template,
                report_format=report_format,
            )

            # Load the series json and extract checks
            with open(subdirectory.joinpath("series.json"), "r", encoding="utf-8") as f:
                series_json = json.load(f)

            entry = {
                "directory": subdirectory
            }

            checks = {}
            for check in series_json["checks"]:
                checks[check["description"]] = check["passed"]

            entry = {**entry, **checks}

            check_results.append(entry)

    pd.DataFrame(check_results).to_csv(directory.joinpath("check_results.csv"), index=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run on all sub-directories in a directory.")
    parser.add_argument(
        "directory",
        type=Path,
        help="The path to process.",
    )
    parser.add_argument(
        "-t",
        "--template",
        type=str,
        help="Template JSON to use for matching.",
    )
    parser.add_argument(
        "-r",
        "--report_format",
        type=str,
        choices=["pdf", "html"],
        help="The format of the report to generate (pdf or html). If not provided, "
        "no report is generated.",
    )

    args = parser.parse_args()

    run_on_all_subdirectories(args.directory, args.template, args.report_format)

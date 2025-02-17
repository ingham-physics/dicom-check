import json
import argparse
from typing import Optional, List, Union
from pathlib import Path

import check_functions
from report import generate_series_report
from utils import load_template


def find_matched_series(series_json: dict, name: Union[str, List[str]]) -> List[dict]:
    matches = []

    if isinstance(name, str):
        name = [name]

    for series in series_json["series"]:
        if "match" in series and series["match"] in name:
            matches.append(series)

    return matches


def perform_checks(directory: Path, template: str, report_format: Optional[str] = None):
    # Load templated
    template = load_template(template)

    # Load series
    with open(directory.joinpath("series.json"), "r", encoding="utf-8") as f:
        series_json = json.load(f)

    checks = template["checks"]

    check_results = []
    for check in checks:
        matched_series = find_matched_series(series_json, check["series"])
        func = getattr(check_functions, check["function"])
        kwargs = check.get("args", {})
        result, output = func(matched_series, **kwargs)

        print(f"Check '{check['description']}' {'passed' if result else 'failed'}")
        if output:
            print(f"  - {output}")

        check_result = {
            "description": check["description"],
            "passed": result,
            "output": output,
            "critical": check.get("critical", False),
        }

        check_results.append(check_result)

    series_json["checks"] = check_results

    with open(directory.joinpath("series.json"), "w", encoding="utf-8") as f:
        json.dump(series_json, f, indent=2)

    if report_format:
        generate_series_report(
            series_json, directory, report_format=report_format, meta=template["meta"]
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess DICOM files.")
    parser.add_argument(
        "directory",
        type=Path,
        help="The path in which DICOM series were preprocessed.",
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

    perform_checks(args.directory, args.template, args.report_format)

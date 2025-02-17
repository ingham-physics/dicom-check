import json
from pathlib import Path
from typing import Optional

import networkx as nx
import pandas as pd

from report import generate_series_report
from utils import load_template

def match_series_to_template(directory: Path, template: str, report_format: Optional[str] = None):
    """Match series in a directory to a template.

    Args:
        directory (Path): The directory containing the series to match.
        template (str): The path to the template JSON file.
        report_format (str): The format of the report to generate (pdf or html). If not
            provided, no report is generated.
    """

    # Load templated
    template = load_template(template)

    # Load series
    with open(directory.joinpath("series.json"), "r", encoding="utf-8") as f:
        series_json = json.load(f)

    # Load series DataFrame
    df = pd.read_csv(directory.joinpath("indexed.csv"))

    expected_series = template["expected_series"]

    expected_graph = nx.DiGraph()
    for series in expected_series:
        expected_graph.add_node(series, **expected_series[series])

        if "referencedSeries" in expected_series[series]:
            expected_graph.add_edge(series, expected_series[series]["referencedSeries"])

    series_graph = nx.DiGraph()
    for series_uid, df_series in df.groupby("series_uid"):
        series_graph.add_node(series_uid, **(df_series.iloc[0].to_dict()))

        if (
            df_series.iloc[0]["referenced_uid"] is not None
            and not pd.isna(df_series.iloc[0]["referenced_uid"])
            and len(df[df["series_uid"] == df_series.iloc[0]["referenced_uid"]]) > 0
        ):
            series_graph.add_edge(series_uid, df_series.iloc[0]["referenced_uid"])

        if df_series.iloc[0]["for_uid"] is not None:
            for for_series_uid, _ in df[
                df.for_uid == df_series.iloc[0]["for_uid"]
            ].groupby("series_uid"):
                if for_series_uid == series_uid:
                    continue
                series_graph.add_edge(series_uid, for_series_uid)

    cc = nx.connected_components(expected_graph.to_undirected())

    matches = {}

    for c in cc:

        sub_graph = expected_graph.subgraph(c)

        # For each expected series, find the corresponding series in the series graph
        for expected_series_name in list(nx.topological_sort(sub_graph)):

            if expected_series_name not in matches:
                matches[expected_series_name] = []

            # Find series with the expected modality
            if len(matches[expected_series_name]) == 0:
                series_can_match = [
                    series_uid
                    for series_uid in series_graph.nodes
                    if series_graph.nodes[series_uid]["modality"]
                    == sub_graph.nodes[expected_series_name]["modality"]
                ]
            else:
                series_can_match = matches[expected_series_name].copy()

            # for each series, check that an edge exist to a series with the expected modality
            for series_uid in series_can_match:

                # find linked series (any direction)
                # print(list(series_graph.successors(series_uid)))
                neighbours = series_graph.neighbors(series_uid)

                # Check the neighbours have the same modality as the expected series neighbours
                expected_neighbours = list(sub_graph.successors(expected_series_name))
                for neighbour in neighbours:
                    for expected_neighbour in expected_neighbours:
                        if (
                            series_graph.nodes[neighbour]["modality"]
                            == sub_graph.nodes[expected_neighbour]["modality"]
                        ):
                            matches[expected_series_name].append(series_uid)

                            if expected_neighbour not in matches:
                                matches[expected_neighbour] = []

                            matches[expected_neighbour].append(neighbour)


    for series_name, matching_series in matches.items():
        print(f"Match for {series_name}: {matching_series}")

    # Update the series json with the matches names
    for match_name, matching_series in matches.items():
        for series_uid in matching_series:
            for series in series_json["series"]:
                if not series["series_uid"] == series_uid:
                    continue

                series["match"] = match_name

    with open(directory.joinpath("series.json"), "w", encoding="utf-8") as f:
        json.dump(series_json, f, indent=2)

    if report_format:
        generate_series_report(series_json, directory, report_format=report_format, meta=template["meta"])

if __name__ == "__main__":
    import argparse

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

    match_series_to_template(args.directory, args.template, args.report_format)

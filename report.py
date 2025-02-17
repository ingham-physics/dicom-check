import logging

from typing import List, Optional, Union
from pathlib import Path

import pandas as pd
import numpy as np
import pydicom

from utils import download_font_pack

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s -%(levelname)s - %(message)s"
)


def fetch_structure_names(ds: pydicom.Dataset) -> List[str]:
    """Fetch the structure names from a DICOM RTSTRUCT file.

    Args:
        ds (pydicom.Dataset): The DICOM dataset.

    Returns:
        List[str]: The list of structure names.
    """

    structure_names = []

    for item in ds.StructureSetROISequence:
        structure_names.append(item.ROIName)

    return structure_names


def parse_nan_value(value: object) -> Optional[object]:
    """Parse a value that may be NaN.

    Args:
        value (object): The value to parse.

    Returns:
        object: The parsed value.
    """
    if pd.isna(value):
        return None
    return value


def generate_series_json(df: pd.DataFrame, meta: Union[List[str], None] = None) -> dict:
    """Generate a JSON object containing series information.

    Args:
        df (pd.DataFrame): The DataFrame containing the series information.
        meta (Union[List[str], None], optional): Additional Meta data to include. Defaults to None.

    Returns:
        dict: The series JSON object.
    """

    pat_ids = df["patient_id"].unique()

    series_json = {
        "patient_id": pat_ids[0],
        "series": [],
    }
    for series_uid, df_series in df.groupby("series_uid", sort=False):
        # Check all the series have the same modality
        if len(df_series["modality"].unique()) > 1:
            raise ValueError(f"Series {series_uid} has multiple modalities")

        # Check all the series have the same date
        if len(df_series["date_time"].unique()) > 1:
            raise ValueError(f"Series {series_uid} has multiple dates")

        # Check all instances in series have the same frame of reference
        if len(df_series["for_uid"].unique()) > 1:
            raise ValueError(f"Series {series_uid} has multiple frame of references")

        # Check all instances in series have the same referenced series
        if len(df_series["referenced_uid"].unique()) > 1:
            raise ValueError(f"Series {series_uid} has multiple referenced series")

        entry = {
            "series_uid": series_uid,
            "modality": df_series["modality"].iloc[0],
            "date_time": df_series["date_time"].iloc[0].isoformat(),
            "frame_of_reference": parse_nan_value(df_series["for_uid"].iloc[0]),
            "referenced_series": parse_nan_value(df_series["referenced_uid"].iloc[0]),
            "instance_count": len(df_series["sop_instance_uid"]),
        }

        if meta is not None:
            for m in meta:
                entry[m] = parse_nan_value(df_series[m].iloc[0])

        # For images, check consistency of slices
        if df_series["modality"].iloc[0] in ["CT", "MR", "PT"]:
            slice_locs = df_series.slice_location.to_numpy()
            slice_locs.sort()
            slice_diffs = np.diff(slice_locs)
            slice_diffs = np.round(slice_diffs, 2)
            slice_diffs = np.unique(slice_diffs)

            if len(slice_diffs) > 1:
                entry["consistent_slice_spacing"] = False
                entry["slice_spacing"] = slice_diffs.tolist()
            else:
                entry["consistent_slice_spacing"] = True
                entry["slice_spacing"] = slice_diffs[0]

            entry["duplicated_slices"] = len(slice_locs) != len(np.unique(slice_locs))

        # Fetch structure names for RTSTRUCT
        if df_series["modality"].iloc[0] == "RTSTRUCT":
            try:
                ds = pydicom.read_file(df_series["file_path"].iloc[0], force=True)
                entry["structure_names"] = fetch_structure_names(ds)
            except Exception as e:  # pylint: disable=broad-except
                logger.error(
                    "Unable to fetch structure names for series %s", series_uid
                )
                logger.error(str(e))

        # Fetch DoseSummationType for RTDOSE
        if df_series["modality"].iloc[0] == "RTDOSE":
            try:
                ds = pydicom.read_file(df_series["file_path"].iloc[0], force=True)
                entry["dose_summation_type"] = ds.DoseSummationType
            except Exception as e:  # pylint: disable=broad-except
                logger.error(
                    "Unable to fetch DoseSummationType for series %s", series_uid
                )
                logger.error(str(e))

        series_json["series"].append(entry)

    return series_json


def generate_series_report(
    series_json: dict,
    output_directory: Path,
    report_format: str = "pdf",
    meta: List[str] = None,
):
    """Generate a report for the series information.

    Args:
        series_json (dict): The series JSON object.
        output_directory (pathlib.Path): The output directory to save the report to.
        report_format (str): The format to save the report in. Default is "pdf".
    """

    if report_format not in ["pdf", "html"]:
        raise ValueError(f"Unsupported format {report_format}")

    if not output_directory.exists():
        output_directory.mkdir(parents=True)

    if report_format == "pdf":
        try:
            from fpdf import FPDF  # pylint: disable=import-outside-toplevel
            from fpdf.enums import XPos, YPos  # pylint: disable=import-outside-toplevel
        except ImportError:
            logger.error(
                "The fpdf package is required for PDF output: pip install fpdf2"
            )
            return

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        if not Path("fonts/DejaVuSansCondensed.ttf").exists():
            download_font_pack(Path("."))
        pdf.add_font("DejaVu", "", "font/DejaVuSansCondensed.ttf", uni=True)
        pdf.add_font("DejaVuBold", "", "font/DejaVuSansCondensed-Bold.ttf", uni=True)
        pdf.add_page()
        pdf.set_font("DejaVu", size=12)

        pdf.cell(
            200,
            5,
            f"DICOM Series Report for {series_json['patient_id']}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="C",
        )

        pdf.ln(5)

        if "checks" in series_json:
            pdf.set_font("DejaVu", size=14)
            pdf.cell(
                200,
                5,
                "Check results",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.set_font("DejaVuBold", size=10)

            pdf.cell(
                200,
                5,
                "Critical checks",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.set_font("DejaVu", size=10)

            for check in series_json["checks"]:
                if not check["critical"]:
                    continue

                mark = "✓" if check["passed"] else "✗"

                pdf.cell(
                    200,
                    5,
                    f" {mark} {check['description']}: {'Passed' if check['passed'] else 'Failed'}",
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                )
                if check["output"]:
                    for part in check["output"].split("\n"):
                        if len(part) == 0:
                            continue
                        pdf.cell(
                            200,
                            5,
                            f"    {part}",
                            new_x=XPos.LMARGIN,
                            new_y=YPos.NEXT,
                        )
            pdf.set_font("DejaVuBold", size=10)

            pdf.cell(
                200,
                5,
                "Other checks",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.set_font("DejaVu", size=10)

            for check in series_json["checks"]:
                if check["critical"]:
                    continue

                mark = "✓" if check["passed"] else "✗"

                pdf.cell(
                    200,
                    5,
                    f" {mark} {check['description']}: {'Passed' if check['passed'] else 'Failed'}",
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                )
                if check["output"]:
                    for part in check["output"].split("\n"):
                        if len(part) == 0:
                            continue
                        pdf.cell(
                            200,
                            5,
                            f"    {part}",
                            new_x=XPos.LMARGIN,
                            new_y=YPos.NEXT,
                        )

            pdf.ln(5)

        pdf.set_font("DejaVu", size=14)
        pdf.cell(
            200,
            5,
            "Series information",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.set_font("DejaVu", size=10)

        for series in series_json["series"]:
            pdf.cell(
                200,
                5,
                f"  - Series UID: {series['series_uid']}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            if "match" in series:
                pdf.set_font("DejaVuBold", size=10)
                pdf.cell(
                    200,
                    5,
                    f"  - Match: {series['match']}",
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                )
                pdf.set_font("DejaVu", size=10)
            pdf.cell(
                200,
                5,
                f"  - Frame of Reference UID: {series['frame_of_reference']}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.cell(
                200,
                5,
                f"  - Referenced Series UID: {series['referenced_series']}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.cell(
                200,
                5,
                f"  - Modality: {series['modality']}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.cell(
                200,
                5,
                f"  - Date/Time: {series['date_time']}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )

            if series["modality"] in ["CT", "MR", "PT"]:
                pdf.cell(
                    200,
                    5,
                    f"  - Slice Spacing: {series['slice_spacing']}",
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                )
                pdf.cell(
                    200,
                    5,
                    f"  - Consistent Slice Spacing: {series['consistent_slice_spacing']}",
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                )
                pdf.cell(
                    200,
                    5,
                    f"  - Duplicated Slices: {series['duplicated_slices']}",
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                )

            if series["modality"] == "RTSTRUCT":
                pdf.cell(
                    200, 5, "  - Structure Names:", new_x=XPos.LMARGIN, new_y=YPos.NEXT
                )
                for name in series["structure_names"]:
                    pdf.cell(
                        200, 5, f"      {name}", new_x=XPos.LMARGIN, new_y=YPos.NEXT
                    )

            if series["modality"] == "RTDOSE":
                pdf.cell(
                    200,
                    5,
                    f"  - Dose Summation Type: {series['dose_summation_type']}",
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                )

            if meta:
                for m in meta:
                    pdf.cell(
                        200,
                        5,
                        f"  - {m}: {series[m]}",
                        new_x=XPos.LMARGIN,
                        new_y=YPos.NEXT,
                    )

            pdf.ln(5)

        pdf.output(output_directory.joinpath("series_report.pdf"))

    elif report_format == "html":
        try:
            import dominate  # pylint: disable=import-outside-toplevel
            from dominate.tags import h1, h2, h3, p, table, tr, td, b  # pylint: disable=import-outside-toplevel
        except ImportError:
            logger.error(
                "The dominate package is required for HTML output: pip install dominate"
            )
            return

        doc = dominate.document(title="DICOM Series Report")

        with doc:
            h1("Series Report")

            if "checks" in series_json:
                h2("Check results")
                h3("Critical checks")
                for check in series_json["checks"]:
                    if not check["critical"]:
                        continue

                    mark = "✓" if check["passed"] else "✗"
                    p(f"{mark} {check['description']}: {'Passed' if check['passed'] else 'Failed'}")
                    if check["output"]:
                        for part in check["output"].split("\n"):
                            if len(part) == 0:
                                continue
                            p(f"    {part}")

                h3("Other checks")
                for check in series_json["checks"]:
                    if check["critical"]:
                        continue

                    mark = "✓" if check["passed"] else "✗"
                    p(f"{mark} {check['description']}: {'Passed' if check['passed'] else 'Failed'}")
                    if check["output"]:
                        for part in check["output"].split("\n"):
                            if len(part) == 0:
                                continue
                            p(f"    {part}")

            h2("Series Information")

            for series in series_json["series"]:
                h3(f"Series UID: {series['series_uid']}")
                if "match" in series:
                    p(b(f"Match: {series['match']}"))

                p(f"Frame of Reference UID: {series['frame_of_reference']}")
                p(f"Referenced Series UID: {series['referenced_series']}")
                p(f"Modality: {series['modality']}")
                p(f"Date/Time: {series['date_time']}")

                if series["modality"] in ["CT", "MR", "PT"]:
                    p(f"Slice Spacing: {series['slice_spacing']}")
                    p(f"Consistent Slice Spacing: {series['consistent_slice_spacing']}")
                    p(f"Duplicated Slices: {series['duplicated_slices']}")

                if series["modality"] == "RTSTRUCT":
                    p("Structure Names:")
                    with table():
                        for name in series["structure_names"]:
                            with tr():
                                td(name)

                if series["modality"] == "RTDOSE":
                    p(f"Dose Summation Type: {series['dose_summation_type']}")

                if meta:
                    for m in meta:
                        p(f"{m}: {series[m]}")

                p()

        with open(
            output_directory.joinpath("series_report.html"), "w", encoding="utf-8"
        ) as f:
            f.write(str(doc))

    logger.info("Generated series report in %s format", report_format)

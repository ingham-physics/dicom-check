import logging
import json
from datetime import datetime
from typing import Union, List, Optional
from pathlib import Path

import pandas as pd
import pydicom
import numpy as np
import tqdm

from report import generate_series_report, generate_series_json
from utils import load_template

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s -%(levelname)s - %(message)s"
)

RT_STRUCTURE_STORAGE_UID = "1.2.840.10008.5.1.4.1.1.481.3"
RT_DOSE_STORAGE_UID = "1.2.840.10008.5.1.4.1.1.481.2"
RT_PLAN_STORAGE_UID = "1.2.840.10008.5.1.4.1.1.481.5"
CT_IMAGE_STORAGE_UID = "1.2.840.10008.5.1.4.1.1.2"
PET_IMAGE_STORAGE_UID = "1.2.840.10008.5.1.4.1.1.128"
MR_IMAGE_STORAGE_UID = "1.2.840.10008.5.1.4.1.1.4"

DICOM_FILE_EXTENSIONS = [
    "dcm",
    "DCM",
    "dcim",
    "DCIM",
    "dicom",
    "DICOM",
]


def determine_dcm_datetime(ds: pydicom.Dataset, require_time: bool = False) -> datetime:
    """Get a date/time value from a DICOM dataset. Will attempt to pull from SeriesDate/SeriesTime
    field first. Will fallback to StudyDate/StudyTime or InstanceCreationDate/InstanceCreationTime
    if not available.

    Args:
        ds (pydicom.Dataset): DICOM dataset
        require_time (bool): Flag to require the time component along with the date

    Returns:
        datetime: The date/time
    """

    date_type_preference = ["Series", "Study", "InstanceCreation"]

    for date_type in date_type_preference:
        type_date = f"{date_type}Date"
        type_time = f"{date_type}Time"
        if type_date in ds and len(ds[type_date].value) > 0:
            if type_time in ds and len(ds[type_time].value) > 0:
                date_time_str = f"{ds[type_date].value}{ds[type_time].value}"
                if "." in date_time_str:
                    return datetime.strptime(date_time_str, "%Y%m%d%H%M%S.%f")

                return datetime.strptime(date_time_str, "%Y%m%d%H%M%S")

            if require_time:
                continue

            return datetime.strptime(ds[type_date].value, "%Y%m%d")

    return None


def scan_file(file: Union[str, Path], meta: List[str]) -> dict:
    """Scan a DICOM file.

    Args:
        file (pathlib.Path|str): The path to the file to scan.

    Returns:
        dict: Returns the dict object containing the scanned information. None if the file
            couldn't be scanned.
        str: Scan result status (ok, error).
        str: Error message if the scan failed.
    """

    res_dict = None
    status = "ok"

    try:
        ds = pydicom.read_file(file, force=True)

        dicom_type_uid = ds.SOPClassUID

        res_dict = {
            "patient_id": ds.PatientID,
            "study_uid": ds.StudyInstanceUID,
            "series_uid": ds.SeriesInstanceUID,
            "modality": ds.Modality,
            "sop_class_uid": dicom_type_uid,
            "sop_instance_uid": ds.SOPInstanceUID,
            "date_time": determine_dcm_datetime(ds),
            "file_path": str(file),
        }

        for m in meta:
            if m in ds:
                res_dict[m] = ds[m].value

        if "FrameOfReferenceUID" in ds:
            res_dict["for_uid"] = ds.FrameOfReferenceUID

        if dicom_type_uid == RT_STRUCTURE_STORAGE_UID:
            try:
                referenced_series_uid = (
                    ds.ReferencedFrameOfReferenceSequence[0]
                    .RTReferencedStudySequence[0]
                    .RTReferencedSeriesSequence[0]
                    .SeriesInstanceUID
                )
                res_dict["referenced_uid"] = referenced_series_uid
            except AttributeError:
                logger.warning("Unable to determine Reference Series UID")

            try:
                # Check other tags for a linked DICOM
                # e.g. ds.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID
                # Potentially, we should check each referenced
                referenced_frame_of_reference_uid = (
                    ds.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID
                )
                res_dict["referenced_for_uid"] = referenced_frame_of_reference_uid

                if "for_uid" not in res_dict:
                    res_dict["for_uid"] = referenced_frame_of_reference_uid
            except AttributeError:
                logger.warning("Unable to determine Referenced Frame of Reference UID")

        elif dicom_type_uid == RT_PLAN_STORAGE_UID:
            try:
                referenced_sop_instance_uid = ds.ReferencedStructureSetSequence[
                    0
                ].ReferencedSOPInstanceUID
                res_dict["referenced_uid"] = referenced_sop_instance_uid
            except AttributeError:
                logger.warning("Unable to determine Reference Series UID")

        elif dicom_type_uid == RT_DOSE_STORAGE_UID:
            try:
                referenced_sop_instance_uid = ds.ReferencedRTPlanSequence[
                    0
                ].ReferencedSOPInstanceUID
                res_dict["referenced_uid"] = referenced_sop_instance_uid
            except AttributeError:
                logger.warning("Unable to determine Reference Series UID")

        elif dicom_type_uid in (
            CT_IMAGE_STORAGE_UID,
            PET_IMAGE_STORAGE_UID,
            MR_IMAGE_STORAGE_UID,
        ):
            image_position = np.array(ds.ImagePositionPatient, dtype=float)
            image_orientation = np.array(ds.ImageOrientationPatient, dtype=float)

            image_plane_normal = np.cross(image_orientation[:3], image_orientation[3:])

            slice_location = (image_position * image_plane_normal)[2]

            res_dict["slice_location"] = slice_location

        logger.debug(
            "Successfully scanned DICOM file with SOP Instance UID: %s",
            res_dict["sop_instance_uid"],
        )

        return res_dict, status, None

    except Exception as e:  # pylint: disable=broad-except
        # Broad except ok here, since we will put these file into a
        # quarantine location for further inspection.
        logger.error("Unable to preprocess file: %s", file)
        error = str(e)

    return res_dict, status, error


def index_dicom_files(
    input_directory: Union[Path, list],
    meta: Union[List[str], None] = None,
    enforce_dcm_ext: bool = True,
) -> pd.DataFrame:
    """Index DICOM files in a directory.

    Args:
        input_directory (pathlib.Path|list): The directory to index.
        meta (list): Additional metadata to include in the index.
        enforce_dcm_ext (bool): Enforce DICOM file extension.

    Returns:
        pd.DataFrame: DataFrame of indexed files.
    """

    if isinstance(input_directory, str):
        input_directory = Path(input_directory)

    if not isinstance(input_directory, Path):
        raise ValueError("input_directory must be of type pathlib.Path or str")

    logger.info("Indexing DICOM files in %s", input_directory)

    if meta is None:
        meta = []

    columns = [
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
    ]

    columns += meta

    files = []

    if enforce_dcm_ext:
        for ext in DICOM_FILE_EXTENSIONS:
            files += list(input_directory.glob(f"**/*.{ext}"))
    else:
        files += list(f for f in input_directory.glob("**/*") if not f.is_dir())

    result_list = []

    for f in tqdm.tqdm(files, desc="Indexing", total=len(files)):
        result, status, error = scan_file(f, meta=meta)

        if status == "error":
            logger.warning("A problem occurred with file %s", f)
            logger.warning("Error: %s", error)
            continue

        if result is not None:
            result_list.append(result)

    df = pd.DataFrame(result_list, columns=columns)

    # Sort the the DataFrame by the patient then series uid and the slice location, ensuring
    # that the slices are ordered correctly
    df = df.sort_values(["patient_id", "modality", "series_uid", "slice_location"])

    logger.info("Indexed %d DICOM files", len(df))

    return df


def preprocess(
    input_directory: Union[Path, list],
    template: Union[str, None] = None,
    enforce_dcm_ext: bool = True,
    report_format: Optional[str] = None,
    output_directory: Optional[Path] = None,
) -> pd.DataFrame:
    """Preprocess DICOM files in a directory.

    Args:
        input_directory (pathlib.Path|list): The directory to preprocess.
        template (str): Path to template file defining meta fields.
        enforce_dcm_ext (bool): Enforce DICOM file extension.
        report_format (str): The format of the report to generate (pdf or html). If not
            provided, no report is generated.
        output_directory (pathlib.Path): The output directory to save the report to. If not
            provided, the input directory will be used.

    Returns:
        pd.DataFrame: DataFrame of indexed files.
    """

    meta = []
    if template is not None:
        template = load_template(template)
        meta = template.get("meta", [])

    if output_directory is None:
        output_directory = input_directory

    # Crawl the DICOM files
    df = index_dicom_files(
        input_directory=input_directory,
        meta=meta,
        enforce_dcm_ext=enforce_dcm_ext,
    )

    # Sort the dataframe by modality, first CT, then MR, then PT, then RTSTRUCT, then
    # RTPLAN, then RTDOSE
    modality_order = ["CT", "MR", "PT", "RTSTRUCT", "RTPLAN", "RTDOSE"]
    for m in df.modality.unique():
        if m not in modality_order:
            modality_order.append(m)
    df["modality"] = pd.Categorical(
        df["modality"], categories=modality_order, ordered=True
    )
    df = df.sort_values(["modality"])

    input_directory.joinpath("indexed.csv").write_text(df.to_csv(index=False))

    # Check we only have one patient
    pat_ids = df["patient_id"].unique()
    if len(pat_ids) > 1:
        raise ValueError(
            f"Only one patient per input directory is expected. Found: {pat_ids}"
        )

    # Prepare a JSON with information on series found
    series_json = generate_series_json(df, meta=meta)

    with open(input_directory.joinpath("series.json"), "w", encoding="utf-8") as f:
        json.dump(series_json, f, indent=2)

    if report_format:
        generate_series_report(series_json, input_directory, report_format, meta)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess DICOM files.")
    parser.add_argument(
        "input_directory",
        type=Path,
        help="The path to the directory containing the DICOM files.",
    )
    parser.add_argument(
        "-t",
        "--template",
        type=str,
        help="Template JSON file defining meta fields to pull.",
    )
    parser.add_argument(
        "--enforce_dcm_ext",
        type=bool,
        default=True,
        help="Enforce DICOM file extension.",
    )
    parser.add_argument(
        "-r",
        "--report_format",
        type=str,
        choices=["pdf", "html"],
        help="The format of the report to generate (pdf or html). If not provided, "
            "no report is generated.",
    )
    parser.add_argument(
        "-o",
        "--output_directory",
        type=Path,
        help="The path to the directory to save the report to. "
        "If not provided, the input directory will be used."
    )

    args = parser.parse_args()

    preprocess(
        input_directory=args.input_directory,
        template=args.template,
        enforce_dcm_ext=args.enforce_dcm_ext,
        report_format=args.report_format,
        output_directory=args.output_directory,
    )

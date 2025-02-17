import json
import requests
import hashlib
import zipfile
from pathlib import Path


def load_template(template_path: Path) -> dict:
    """Load a JSON template file.

    Args:
        template_path (Path): Path to the template file.

    Returns:
        dict: The loaded template.
    """
    with open(template_path, "r", encoding="utf-8") as file:
        return json.load(file)


def download_file(url: str, expected_hash: str, output_path: Path):
    """Download a zip file from a URL and verify its hash.

    Args:
        url (str): The URL to download the file from.
        expected_hash (str): The expected hash of the file.
        output_path (Path): The path to save the downloaded file.
    """

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    with open(output_path, "wb") as file:
        file.write(response.content)

    file_hash = hashlib.md5()
    with open(output_path, "rb") as file:
        while chunk := file.read(4096):
            file_hash.update(chunk)

    if file_hash.hexdigest() != expected_hash:
        raise ValueError("Hash mismatch")

def download_font_pack(output_path: Path):
    """Download a font pack required for PDF generation.

    Args:
        output_path (Path): The path to save the downloaded font pack.
    """

    output_path.mkdir(exist_ok=True)

    download_file(
        "https://github.com/reingart/pyfpdf/releases/download/binary/fpdf_unicode_font_pack.zip",
        "430c54cf9cd250f5809bcf76d06e41af",
        output_path.joinpath("font_pack.zip")
    )

    # Unzip file
    with zipfile.ZipFile(output_path.joinpath("font_pack.zip"), "r") as zip_ref:
        zip_ref.extractall(output_path)

    # Remove zip file
    output_path.joinpath("font_pack.zip").unlink()

def download_test_data(output_path: Path):
    """Download test data for the application.

    Args:
        output_path (Path): The path to save the downloaded test data.
    """

    output_path.mkdir(exist_ok=True)

    download_file(
        "https://zenodo.org/record/5276878/files/HNSCC.zip",
        "6332d59406978a92f57d15da84f2e143",
        output_path.joinpath("HNSCC.zip")
    )

    # Unzip file
    with zipfile.ZipFile(output_path.joinpath("HNSCC.zip"), "r") as zip_ref:
        zip_ref.extractall(output_path)

    # Remove zip file
    output_path.joinpath("HNSCC.zip").unlink()

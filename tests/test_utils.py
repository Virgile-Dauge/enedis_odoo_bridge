import pytest
import re
from pathlib import Path
from zipfile import ZipFile
from datetime import date
from dotenv import load_dotenv
from enedis_odoo_bridge.utils import gen_dates, pro_rata, unzip, download

__author__ = "Virgile"
__copyright__ = "Virgile"
__license__ = "GPL-3.0-only"


def test_gen_dates_generic():
    current_date = date(2022, 10, 15)
    expected_start_date, expected_end_date = gen_dates(current_date)

    assert expected_start_date.year == 2022
    assert expected_start_date.month == 9
    assert expected_start_date.day == 1

    assert expected_end_date.year == 2022
    assert expected_end_date.month == 9
    assert expected_end_date.day == 30

def test_gen_dates_january():
    current_date = date(2022, 1, 15)
    expected_start_date, expected_end_date = gen_dates(current_date)
    assert expected_start_date.month == 12
    assert expected_start_date.year == 2021

    assert expected_end_date.month == 12
    assert expected_end_date.year == 2021

def test_pro_rata_same_month():
    start_date = date(2022, 1, 15)
    end_date = date(2022, 1, 30)
    assert pro_rata(start_date, end_date) == 16/31

def test_pro_rata_next_month():
    start_date = date(2022, 1, 15)
    end_date = date(2022, 2, 15)
    assert pro_rata(start_date, end_date) == 17/31 + 15/28

def test_pro_rata_different_years():
    start_date = date(2022, 12, 15)
    end_date = date(2023, 1, 15)
    assert pro_rata(start_date, end_date) == 17/31 + 15/31

def test_pro_rata_invalid_dates():
    with pytest.raises(ValueError):
        pro_rata(date(2022, 1, 15), date(2021, 1, 15))


def test_unzip_no_file():
    with pytest.raises(FileNotFoundError):
        extracted_dir = unzip("test_data.zip")

def test_unzip_function():
    # Create a temporary zip file for testing
    with ZipFile("test_data.zip", "w") as zip_file:
        zip_file.writestr("test_file.txt", "This is a test file.")

    # Call the function to be tested
    extracted_dir = unzip("test_data.zip")

    # Check if the function extracted the contents of the zip file to the specified directory
    assert extracted_dir.exists()
    assert extracted_dir.joinpath("test_file.txt").exists()

    # Clean up the temporary zip file
    Path("test_data.zip").unlink()

def test_download_invalid_type():
    tasks = ['InvalidType']
    load_dotenv()
    with pytest.raises(ValueError, match=re.escape("Type InvalidType not found in ['R15', 'C15', 'F15']")):
        download(tasks)
import pytest
from datetime import date
from pathlib import Path
from enedis_odoo_bridge.enedis_flux_reader.flux_repository.r151_flux_repository import select_zip_by_date

@pytest.fixture
def zip_files():
    return [
        Path("file_20230101000000.zip"),
        Path("file_20230103000000.zip"),
        Path("file_20230105000000.zip"),
        Path("file_20230107000000.zip")
    ]

def test_select_zip_by_date_no_end_date(zip_files):
    start_date = date(2023, 1, 1)
    result = select_zip_by_date(zip_files, start_date)
    expected = [Path("file_20230103000000.zip")]
    assert result == expected

def test_select_zip_by_date_with_end_date(zip_files):
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 5)
    result = select_zip_by_date(zip_files, start_date, end_date)
    expected = [Path("file_20230103000000.zip"), Path("file_20230105000000.zip"), Path("file_20230107000000.zip")]
    assert result == expected

def test_select_zip_by_date_no_matching_files(zip_files):
    start_date = date(2023, 1, 10)
    result = select_zip_by_date(zip_files, start_date)
    expected = []
    assert result == expected

def test_select_zip_by_date_with_end_date_no_matching_files(zip_files):
    start_date = date(2022, 1, 1)
    end_date = date(2022, 12, 23)
    result = select_zip_by_date(zip_files, start_date, end_date)
    expected = []
    assert result == expected

def test_select_zip_by_date_edge_case(zip_files):
    start_date = date(2023, 1, 3)
    end_date = date(2023, 1, 5)
    result = select_zip_by_date(zip_files, start_date, end_date)
    expected = [Path("file_20230105000000.zip"), Path("file_20230107000000.zip")]
    assert result == expected
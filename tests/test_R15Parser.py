import pytest
from pathlib import Path
from datetime import datetime
from enedis_odoo_bridge.R15Parser import R15Parser, get_meta

__author__ = "Virgile"
__copyright__ = "Virgile"
__license__ = "GPL-3.0-only"

def test_get_meta_with_zip_suffix():
    file_path = Path('test_data/1_R15_2_3_4-5_6_20240407050942.zip')
    expected_result = {'path': file_path, 'emetteur': '1', 'Type': 'R15', 
                       'destinataire': '2', 'num_contrat': '3', 
                       'Instance_GRD': '4-5', 'num_seq': '6', 
                       'date': datetime(2024, 4, 7, 5, 9, 42)}
    result = get_meta(file_path)
    assert result == expected_result

def test_get_meta_with_xml_suffix():
    file_path = Path('test_data/1_R15_2_3_4-5_6_7_8.xml')
    expected_result = {'path': file_path, 'emetteur': '1', 'Type': 'R15', 
                       'destinataire': '2', 'num_contrat': '3', 
                       'Instance_GRD': '4-5', 'num_seq': '6',
                       'XXXXX': '7', 'YYYYY': '8'}
    result = get_meta(file_path)
    assert result == expected_result

def test_get_meta_without_zip_or_xml_suffix():
    file_path = Path('test_data/file_with_wrong_suffix.txt')
    with pytest.raises(ValueError):
        get_meta(file_path)



@pytest.fixture
def test_file_path() -> Path:
    return Path(__file__).parent.joinpath('test_files', 'test_file.zip')

def test_init_with_invalid_file_path(test_file_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        R15Parser('invalid_file_path.zip')

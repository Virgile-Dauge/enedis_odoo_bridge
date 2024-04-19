import pytest
import re
import os
from pathlib import Path
import tempfile
from zipfile import ZipFile
from datetime import date
from dotenv import load_dotenv
from unittest.mock import patch, MagicMock

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from pathlib import Path

from enedis_odoo_bridge.utils import decrypt_file
from enedis_odoo_bridge.utils import load_prefixed_dotenv
from enedis_odoo_bridge.utils import gen_dates, pro_rata, unzip, download, is_valid_json, calculate_checksum, file_changed

__author__ = "Virgile"
__copyright__ = "Virgile"
__license__ = "GPL-3.0-only"

import pytest
from enedis_odoo_bridge.utils import check_required

def test_check_required_all_keys_present():
    # Setup
    config = {'URL': 'http://example.com', 'DB': 'test_db', 'USERNAME': 'user', 'PASSWORD': 'pass'}
    required = ['URL', 'DB', 'USERNAME', 'PASSWORD']
    
    # Exercise
    result = check_required(config, required)
    
    # Verify
    assert result == config, "The function should return the original config when all required keys are present."

def test_check_required_missing_key():
    # Setup
    config = {'URL': 'http://example.com', 'DB': 'test_db', 'USERNAME': 'user'}
    required = ['URL', 'DB', 'USERNAME', 'PASSWORD']
    
    # Exercise & Verify
    with pytest.raises(ValueError) as excinfo:
        check_required(config, required)
    
    assert "Required parameter PASSWORD not found" in str(excinfo.value), "The function should raise ValueError with a message indicating the missing key."
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
        extracted_dir = unzip(Path("test_data.zip"))

def test_unzip_function():
    # Create a temporary zip file for testing
    with ZipFile("test_data.zip", "w") as zip_file:
        zip_file.writestr("test_file.txt", "This is a test file.")

    # Call the function to be tested
    extracted_dir = unzip(Path("test_data.zip"))

    # Check if the function extracted the contents of the zip file to the specified directory
    assert extracted_dir.exists()
    assert extracted_dir.joinpath("test_file.txt").exists()

    # Clean up the temporary zip file
    Path("test_data.zip").unlink()

def test_download_invalid_type():
    tasks = ['InvalidType']
    load_dotenv()
    with pytest.raises(KeyError):
        download({'FTP_ADDRESS':1, 'FTP_USER':2, 'FTP_PASSWORD':3,
                  'FTP_R15_DIR':4, 'FTP_C15_DIR':5, 'FTP_F15_DIR':6,}, tasks)

def test_load_prefixed_dotenv_missing_required():
    # Mock the environment variables with a missing required key
    with patch.dict('os.environ', {'EOB_URL': 'http://example.com', 'EOB_USERNAME': 'user'}):
        # Define the required keys, including a key that is not present in the environment
        required = ['URL', 'USERNAME', 'PASSWORD']
        
        # Verify that calling the function with a missing required key raises a ValueError
        with pytest.raises(ValueError) as excinfo:
            load_prefixed_dotenv(prefix='EOB_', required=required)
        
        assert "Required parameter PASSWORD not found" in str(excinfo.value), "The function should raise ValueError when a required key is missing."

def test_calculate_checksum():
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        content = b"Hello, world!"
        tmpfile.write(content)
        tmpfile.flush()

        # Calculate the checksum of the temporary file
        calculated_checksum = calculate_checksum(Path(tmpfile.name))

        # Expected checksum calculated using an external tool (e.g., `echo -n "Hello, world!" | sha256sum` on Linux)
        expected_checksum = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"

        # Verify that the calculated checksum matches the expected checksum
        assert calculated_checksum == expected_checksum, "The calculated checksum does not match the expected checksum."

        # Clean up the temporary file
        Path(tmpfile.name).unlink()

def test_file_changed():
    # Setup: Create a temporary file and write initial content
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        tmpfile_path = Path(tmpfile.name)
        initial_content = b"Initial content"
        tmpfile.write(initial_content)
        tmpfile.flush()

    # Calculate the checksum of the initial content
    initial_checksum = calculate_checksum(tmpfile_path)

    # Modify the file by appending new content
    with open(tmpfile_path, "ab") as tmpfile:
        tmpfile.write(b" - modified")

    # Exercise: Check if the file has changed by comparing checksums
    file_has_changed = file_changed(tmpfile_path, initial_checksum)

    # Verify: The function should return True since the file content has changed
    assert file_has_changed, "The function should detect that the file content has changed."

    # Teardown: Remove the temporary file
    os.remove(tmpfile_path)

def test_is_valid_json_with_valid_json():
    valid_json_string = '{"name": "John", "age": 30, "city": "New York"}'
    assert is_valid_json(valid_json_string) == True, "The function should return True for valid JSON strings."

def test_is_valid_json_with_invalid_json():
    invalid_json_string = '{"name": "John", "age": 30, "city": "New York"'
    assert is_valid_json(invalid_json_string) == False, "The function should return False for invalid JSON strings."

def test_is_valid_json_with_empty_string():
    empty_json_string = ''
    assert is_valid_json(empty_json_string) == False, "The function should return False for empty strings."

def test_is_valid_json_with_non_json_string():
    non_json_string = 'This is not a JSON string.'
    assert is_valid_json(non_json_string) == False, "The function should return False for non-JSON strings."


def test_decrypt_file():
    # Setup: Create a temporary encrypted file
    original_content = b"This is a test."
    key = get_random_bytes(16)  # AES key must be either 16, 24, or 32 bytes long
    iv = get_random_bytes(16)  # IV must be 16 bytes long for AES
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_content = cipher.encrypt(original_content.ljust(16, b'\0'))  # Padding to ensure the content is a multiple of 16 bytes

    temp_encrypted_file = Path("temp_encrypted_file.bin")
    with temp_encrypted_file.open("wb") as f:
        f.write(encrypted_content)

    # Exercise: Decrypt the file
    decrypted_file_path = decrypt_file(temp_encrypted_file, key, iv)

    # Verify: Check if the decrypted content matches the original content
    with decrypted_file_path.open("rb") as f:
        decrypted_content = f.read().rstrip(b'\0')  # Remove padding
        assert decrypted_content == original_content, "Decrypted content does not match the original content."

    # Teardown: Remove temporary files
    temp_encrypted_file.unlink()
    decrypted_file_path.unlink()
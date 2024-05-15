import pytest
import re
import os
from pathlib import Path
import tempfile
from zipfile import ZipFile
from datetime import date
from dotenv import load_dotenv
from unittest.mock import patch, MagicMock
from calendar import monthrange

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from pathlib import Path

from enedis_odoo_bridge.utils import decrypt_file
from enedis_odoo_bridge.utils import load_prefixed_dotenv
from enedis_odoo_bridge.utils import gen_dates, pro_rata, unzip, is_valid_json, calculate_checksum, file_changed

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

def test_gen_dates_no_current_date():
    # Test for when no date is provided; it should default to the previous month from today
    # This test might be a bit tricky since it depends on when the test is run
    # One approach is to manually calculate what the expected result should be based on today's date
    today = date.today()
    if today.month == 1:
        expected_year = today.year - 1
        expected_month = 12
    else:
        expected_year = today.year
        expected_month = today.month - 1

    expected_start_date = date(expected_year, expected_month, 1)
    expected_end_date = date(expected_year, expected_month, monthrange(expected_year, expected_month)[1])

    assert gen_dates(None) == (expected_start_date, expected_end_date), "Failed to calculate dates when no current date is provided"

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

@pytest.fixture
def mock_sftp_connection():
    with patch('sftpretty.Connection') as mock:
        yield mock

@pytest.fixture
def config():
    return {
        'FTP_ADDRESS': 'ftp.example.com',
        'FTP_USER': 'user',
        'FTP_PASSWORD': 'password',
        'FTP_R15_DIR': 'R15',
        'FTP_C15_DIR': 'C15',
        'FTP_F15_DIR': 'F15',
    }

""" def test_download_single_task(mock_sftp_connection, config):
    tasks = ['R15']
    local_path = Path('/tmp/data/flux_enedis/')  # Adjust the path as needed

    # Mock the behavior of the sftp connection and its methods
    mock_sftp_connection.return_value.__enter__.return_value.get_d = MagicMock()

    # Execute the function with the mocked connection
    result = download(config, tasks, local_path)

    # Verify that the function returns the correct paths
    assert tasks[0] in result
    assert result[tasks[0]] == local_path.joinpath(tasks[0]).expanduser()

    # Verify that the sftp get_d method was called with the correct parameters
    mock_sftp_connection.return_value.__enter__.return_value.get_d.assert_called_once_with(
        '/flux_enedis/' + config[f'FTP_{tasks[0]}_DIR'],
        local_path.joinpath(tasks[0]).expanduser(),
        resume=True,
        workers=10
    ) 

def test_download_invalid_task_raises_value_error(mock_sftp_connection, config):
    tasks = ['INVALID']
    local_path = Path('/tmp/data/flux_enedis/')  # Adjust the path as needed

    # Since the function is expected to raise a ValueError for an invalid task,
    # we don't need to mock the behavior of the sftp connection for this test.

    with pytest.raises(KeyError):
        download(config, tasks, local_path)
def test_download_invalid_type():
    tasks = ['InvalidType']
    load_dotenv()
    with pytest.raises(KeyError):
        download({'FTP_ADDRESS':1, 'FTP_USER':2, 'FTP_PASSWORD':3,
                  'FTP_R15_DIR':4, 'FTP_C15_DIR':5, 'FTP_F15_DIR':6,}, tasks)
"""
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


def test_decrypt_file_no_prefix():
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

def test_decrypt_file_with_prefix():
    # Setup: Create a temporary prefixed filePath
    temp_prefixed_file = Path("decrypted_file.zip")
    key = get_random_bytes(16)  # AES key must be either 16, 24, or 32 bytes long
    iv = get_random_bytes(16)  # IV must be 16 bytes long for AES

    # Exercise: Decrypt the file
    decrypted_file_path = decrypt_file(temp_prefixed_file, key, iv, 'decrypted_')

    # Verify: Check if the decrypted content matches the original content
    assert decrypted_file_path == temp_prefixed_file, "Decrypted file path does not match the original file path."
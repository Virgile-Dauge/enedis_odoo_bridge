import os
import zipfile

from dotenv import load_dotenv
from pathlib import Path

from datetime import date, datetime
from calendar import monthrange
import hashlib
import json
from Crypto.Cipher import AES
from typing import Union, Any
from rich.progress import Progress
import pandas as pd
from pandas import Timestamp
import paramiko
import logging
logging.getLogger("paramiko.transport").setLevel(logging.ERROR)
_logger = logging.getLogger('enedis_odoo_bridge')

class CustomLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return f'{self.extra["prefix"]}{msg}', kwargs

def check_required(config: dict[str, str], required: list[str]):
    for r in required:
        if r not in config.keys():
            raise ValueError(f'Required parameter {r} not found in {config.keys()} from .env file.')
    return config

def load_prefixed_dotenv(prefix: str='EOB_', required: list[str]=[]) -> dict[str, str]:
    # Load the .env file
    load_dotenv()

    # Retrieve all environment variables
    env_variables = dict(os.environ)
    
    return check_required({k.replace(prefix, ''): v for k, v in env_variables.items() if k.startswith(prefix)}, required)

def gen_dates(current: Union[date, None]) -> tuple[date, date]:
    if not current:
        current = date.today()
    
    if current.month == 1:
        current = current.replace(month=12, year=current.year-1)
    else:
        current = current.replace(month=current.month-1)

    starting_date = current.replace(day=1)
    ending_date = current.replace(day = monthrange(current.year, current.month)[1])
    return starting_date, ending_date

def gen_Timestamps(current: Union[date, None]) -> tuple[Timestamp, Timestamp]:
    start_date, ending_date = gen_dates(current)

    start_TimeStamps = pd.to_datetime(datetime.combine(start_date, datetime.min.time())).tz_localize('Etc/GMT-2')
    end_TimeStamps = pd.to_datetime(datetime.combine(ending_date, datetime.max.time())).tz_localize('Etc/GMT-2')
    return start_TimeStamps, end_TimeStamps

def pro_rata(start: date, end: date) -> float:

    if end < start or (abs(end.month-start.month)> 1 and not (end.year-start.year==1 and start.month==12 and end.month==1)):
        raise ValueError(f'Dates are not valid, end month must be same or next month of start month : {start} - {end}')
    
    if start.month == end.month:
        return (end.day-start.day+1)/monthrange(start.year, start.month)[1]
    
    x = (monthrange(start.year, start.month)[1]+1 - start.day)/monthrange(start.year, start.month)[1]
    y = (end.day)/monthrange(end.year, end.month)[1]
    return  x + y

def unzip(zip_path: Path) -> Path:
    """
    Extracts the contents of the given zip file to a specified directory.

    Parameters:
    zip_path (str): The path to the zip file to be extracted.

    Returns:
    Path: The path to the directory where the contents of the zip file were extracted.

    Raises:
    FileNotFoundError: If the specified zip file does not exist.

    This function uses the built-in `zipfile` module to extract the contents of the zip file to a specified directory. It first creates the specified directory if it does not already exist. Then, it extracts the contents of the zip file to that directory.

    Example:
    ```python
    extracted_dir = unzip('/path/to/myfile.zip')
    print(extracted_dir)  # Output: '/path/to/myfile/'
    ```
    """
    if not zip_path.exists():
        raise FileNotFoundError(f'File {zip_path} not found.')
    
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        out = Path(zip_path).parent.joinpath(Path(zip_path).stem)
        #print(f'creating {out} directory and extracting')
        out.mkdir(exist_ok=True)

        zip_ref.extractall(out)
        return out
    
def download_new_files(config: dict[str, str], tasks: list[str], local: Path) -> dict[str, Path]:
    """
    Downloads specified directories from the SFTP server using paramiko, skipping files that already exist locally.

    Parameters:
    config (dict[str, str]): Configuration dictionary containing SFTP details.
    tasks (List[str]): list of directory types to download (e.g., ['R15', 'C15']).
    local (Path): The local root path to save downloaded files. Defaults to '~/data/flux_enedis/'.

    Returns:
    dict[str, Path]: A dictionary mapping each task to its local path containing downloaded files.
    """
    required =  ['FTP_ADDRESS', 'FTP_USER', 'FTP_PASSWORD',]+[f'FTP_{k}_DIR' for k in tasks]
    config = check_required(config, required)
    completed_tasks = {}

    transport = paramiko.Transport((config['FTP_ADDRESS'], 22))
    transport.connect(username=config['FTP_USER'], password=config['FTP_PASSWORD'])
    sftp = paramiko.SFTPClient.from_transport(transport)

    for type in tasks:
        distant = '/flux_enedis/' + str(config[f'FTP_{type}_DIR'])
        local_dir = local.joinpath(type).expanduser()
        if not local_dir.exists():
            local_dir.mkdir(parents=True, exist_ok=True)

        # Get a list of all existing files in local_dir and its subdirectories
        existing_files = {file.name for file in local_dir.rglob('*') if file.is_file()}

        try:
            files_to_download = sftp.listdir(distant)
            local_files = []
            for file_name in files_to_download:
                if file_name not in existing_files:
                    remote_file_path = os.path.join(distant, file_name)
                    local_file_path = local_dir.joinpath(file_name)
                    sftp.get(remote_file_path, str(local_file_path))
                    local_files.append(local_file_path)
        except Exception as e:
            _logger.error(f"Failed to download files from {distant}: {e}")

        completed_tasks[type] = local_files

    sftp.close()
    transport.close()

    return completed_tasks

def download_new_files_with_progress(config: dict[str, str], tasks: list[str], local: Path) -> list[Path]:
    """
    Downloads specified directories from the SFTP server using paramiko, skipping files that already exist locally.
    Now includes progress tracking with rich.

    Parameters:
    config (dict[str, str]): Configuration dictionary containing SFTP details.
    tasks (list[str]): list of directory types to download (e.g., ['R15', 'C15']).
    local (Path): The local root path to save downloaded files. Defaults to '~/data/flux_enedis/'.

    Returns:
    dict[str, Path]: A dictionary mapping each task to its local path containing downloaded files.
    """
    required =  ['FTP_ADDRESS', 'FTP_USER', 'FTP_PASSWORD',]+[f'FTP_{k}_DIR' for k in tasks]
    config = check_required(config, required)
    completed_tasks = {}

    transport = paramiko.Transport((config['FTP_ADDRESS'], 22))
    transport.connect(username=config['FTP_USER'], password=config['FTP_PASSWORD'])
    sftp = paramiko.SFTPClient.from_transport(transport)

    local_files = []
    for type in tasks:
        distant = '/flux_enedis/' + str(config[f'FTP_{type}_DIR'])
        local_dir = local.joinpath(type).expanduser()
        if not local_dir.exists():
            local_dir.mkdir(parents=True, exist_ok=True)

        existing_files = {file.name for file in local_dir.rglob('*') if file.is_file()}

        try:
            files_to_download = [f for f in sftp.listdir(distant) if f not in existing_files]
            with Progress() as progress:
                task = progress.add_task(f"[green]Downloading {len(files_to_download)} {type} files...", total=len(files_to_download))
                
                for file_name in files_to_download:
                    remote_file_path = os.path.join(distant, file_name)
                    local_file_path = local_dir.joinpath(file_name)
                    # Update progress bar with each file download
                    sftp.get(remote_file_path, str(local_file_path), callback=lambda x, y: progress.update(task, advance=1))
                    local_files.append(local_file_path)
        except Exception as e:
            _logger.error(f"Failed to download files from {distant}: {e}")
 
    sftp.close()
    transport.close()

    return local_files

def calculate_checksum(file_path: Path) -> str:
    # Initialize SHA-256 hash object
    sha256 = hashlib.sha256()

    # Open file in binary mode
    with open(file_path, "rb") as file:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: file.read(4096), b""):
            # Update hash object with current chunk
            sha256.update(chunk)

    # Return hexadecimal representation of hash
    return sha256.hexdigest()

def file_changed(file_path: Path, stored_checksum: str) -> bool:
    # Calculate checksum of current archive
    current_checksum = calculate_checksum(file_path)

    # Compare current checksum with stored checksum
    return current_checksum != stored_checksum

def is_valid_json(json_string: str) -> bool:
    try:
        # Essayez de charger le JSON
        json.loads(json_string)
    except ValueError as e:
        # Si une erreur se produit, le JSON n'est pas valide
        return False
    return True

def decrypt_file(file_path: Path, key: bytes, iv: bytes, prefix: str="decrypted_") -> Path:
    if prefix in file_path.stem:
        return file_path
    # Initialize the AES cipher with CBC mode
    cipher = AES.new(key, AES.MODE_CBC, iv)
    output_file = file_path.with_name(prefix + file_path.stem + ".zip")
    # Decrypt the input file and write the decrypted content to the output file
    with file_path.open("rb") as f_in, output_file.open("wb") as f_out:
        decrypted_data = cipher.decrypt(f_in.read())
        f_out.write(decrypted_data)
    return output_file

def recursively_decrypt_zip_files(directory: Path, key: bytes, iv: bytes, prefix:str):
    """
    Recursively decrypts all ZIP files in the specified directory that are not already decrypted.

    Parameters:
    directory (Path): The directory to search for ZIP files.
    key (bytes): The AES key for decryption.
    iv (bytes): The AES initialization vector for decryption.
    """
    for file in directory.rglob('*.zip'):  # Recursively find all ZIP files
        if not file.stem.startswith('decrypted_'):  # Check if the file is not already decrypted
            decrypted_file_path = decrypt_file(file, key, iv, prefix=prefix)

def recursively_decrypt_zip_files_with_progress(directory: Path, key: bytes, iv: bytes, prefix:str)-> list[Path]:
    """
    Recursively decrypts all ZIP files in the specified directory that are not already decrypted.

    Parameters:
    directory (Path): The directory to search for ZIP files.
    key (bytes): The AES key for decryption.
    iv (bytes): The AES initialization vector for decryption.
    """
    files_to_decrypt = [f for f in directory.rglob('*.zip') if not f.stem.startswith('decrypted_')]
    decrypted_files = []
    with Progress() as progress:
        task = progress.add_task(f"[green]Decrypting {len(files_to_decrypt)} files...", total=len(files_to_decrypt))
        for f in files_to_decrypt:
            decrypted_files += [decrypt_file(f, key, iv, prefix=prefix)]
            progress.update(task, advance=1)
    return decrypted_files
